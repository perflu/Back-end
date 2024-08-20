import os
import requests
import json
import csv

class ClovaSpeechClient:
    invoke_url = 'https://clovaspeech-gw.ncloud.com/external/v1/8749/90e770d5b5adf68d9e2fc484ee680fa7a69fb40540bcffe37be6c6921dcd6a42'
    secret = 'd569e2e69b9543928bceac30ce2fe43c'

    def __init__(self):
        self.headers = {
            'X-CLOVASPEECH-API-KEY': self.secret
        }

    def req_upload(self, file, completion, **kwargs):
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            **kwargs
        }
        with open(file, 'rb') as f:
            files = {
                'media': f,
                'params': (None, json.dumps(request_body).encode('utf-8'), 'application/json')
            }
            response = requests.post(headers=self.headers, url=self.invoke_url + '/recognizer/upload', files=files)

        # 응답 상태 코드 확인
        if response.status_code != 200:
            print(f"Clova Speech API 호출 오류: {response.status_code} - {response.text}")
            return None

        response_json = response.json()
        if not response_json.get('segments'):
            print("Clova Speech API 응답에 유효한 'segments' 데이터가 없습니다.")
            return None

        return response_json

    def save_response(self, response_json, filename, output_format, target_lang):
        if output_format == 'srt':
            self.save_response_to_srt(response_json, filename, target_lang)
        elif output_format == 'smi':
            self.save_response_to_smi(response_json, filename, target_lang)
        elif output_format == 'txt':
            self.save_response_to_txt(response_json, filename, target_lang)
        elif output_format == 'csv':
            self.save_response_to_csv(response_json, filename, target_lang)
        else:
            print("지원되지 않는 형식입니다.")

    def save_response_to_srt(self, response_json, filename, target_lang):
        try:
            with open(filename, 'w', encoding='utf-8') as srt_file:
                index = 1
                for segment in response_json.get('segments', []):
                    start_time = segment['start']
                    end_time = segment['end']
                    text = segment['text']

                    translation = self.translate_text(text, target_lang)

                    start_time_srt = self.convert_millis_to_srt_time(start_time)
                    end_time_srt = self.convert_millis_to_srt_time(end_time)

                    srt_file.write(f"{index}\n")
                    srt_file.write(f"{start_time_srt} --> {end_time_srt}\n")
                    srt_file.write(f"{translation}\n\n")
                    index += 1

            print(f"응답이 {filename} 파일로 저장되었습니다.")
        except Exception as e:
            print(f"SRT 저장 중 오류가 발생했습니다: {e}")

    def save_response_to_smi(self, response_json, filename, target_lang):
        try:
            with open(filename, 'w', encoding='utf-8') as smi_file:
                smi_file.write('<SAMI>\n<HEAD>\n<STYLE TYPE="text/css">\n<!--\nP { margin-left:2pt; margin-right:2pt; margin-bottom:1pt; margin-top:1pt; font-size:20pt; text-align:center; font-family:Verdana; color:white; background-color:black; }\n-->\n</STYLE>\n</HEAD>\n<BODY>\n')
                for segment in response_json.get('segments', []):
                    start_time = segment['start']
                    end_time = segment['end']
                    text = segment['text']

                    translation = self.translate_text(text, target_lang)

                    start_time_smi = self.convert_millis_to_srt_time(start_time)
                    end_time_smi = self.convert_millis_to_srt_time(end_time)

                    smi_file.write(f"<SYNC Start={start_time_smi}><P Class=KRCC>{translation}</P>\n")
                    smi_file.write(f"<SYNC Start={end_time_smi}><P Class=KRCC>&nbsp;</P>\n")
                smi_file.write('</BODY>\n</SAMI>')

            print(f"응답이 {filename} 파일로 저장되었습니다.")
        except Exception as e:
            print(f"SMI 저장 중 오류가 발생했습니다: {e}")

    def save_response_to_txt(self, response_json, filename, target_lang):
        try:
            with open(filename, 'w', encoding='utf-8') as txt_file:
                for segment in response_json.get('segments', []):
                    text = segment['text']

                    translation = self.translate_text(text, target_lang)

                    txt_file.write(f"{translation}\n\n")

            print(f"응답이 {filename} 파일로 저장되었습니다.")
        except Exception as e:
            print(f"TXT 저장 중 오류가 발생했습니다: {e}")

    def save_response_to_csv(self, response_json, filename, target_lang):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['Index', 'Start Time', 'End Time', f'Text ({target_lang})'])

                index = 1
                for segment in response_json.get('segments', []):
                    start_time_srt = self.convert_millis_to_srt_time(segment['start'])
                    end_time_srt = self.convert_millis_to_srt_time(segment['end'])
                    text = segment['text']

                    translation = self.translate_text(text, target_lang)

                    csv_writer.writerow([index, start_time_srt, end_time_srt, translation])
                    index += 1

            print(f"응답이 {filename} 파일로 저장되었습니다.")
        except Exception as e:
            print(f"CSV 저장 중 오류가 발생했습니다: {e}")

    def translate_text(self, text, target_lang):
        try:
            translator = DeepLTranslator()
            return translator.translate_text(text, target_lang)
        except Exception as e:
            print(f"번역 중 오류가 발생했습니다: {e}")
            return text

    @staticmethod
    def convert_millis_to_srt_time(millis):
        seconds, milliseconds = divmod(millis, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"


class DeepLTranslator:
    api_url = "https://api.deepl.com/v2/translate"  # DeepL Pro API URL
    api_key = "your_deepl_pro_api_key_here"  # DeepL Pro API Key

    def translate_text(self, text, target_lang):
        data = {
            'auth_key': self.api_key,
            'text': text,
            'target_lang': target_lang
        }
        response = requests.post(self.api_url, data=data)
        if response.status_code == 200:
            result = response.json()
            return result['translations'][0]['text']
        else:
            print(f"DeepL API 호출 오류: {response.status_code}")
            return text


def process_video(file_path, target_lang, output_format):
    clova_client = ClovaSpeechClient()
    res_json = clova_client.req_upload(file=file_path, completion='sync')

    if res_json:
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        output_filename = f"{base_filename}.{output_format}"

        clova_client.save_response(res_json, output_filename, output_format, target_lang)


if __name__ == '__main__':
    file_path = input("동영상 파일 경로를 입력하세요: ")
    target_lang = input("번역할 언어를 선택하세요 (EN, JA, ZH, RU, ES, DE): ").upper()
    output_format = input("출력할 파일 형식을 선택하세요 (srt, smi, txt, csv): ").lower()

    process_video(file_path, target_lang, output_format)
