# pip install coolsms-python-sdk==2.0.3
import sys
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
import pandas as pd

def sendMessage(btn_name):
  # api_key, secret설정
  api_key = "NCSSTF3LTXVTVZAE"
  api_secret = "RPNJEHR1MDK5EWOQUD7XVFDGX89EGJHP"

  # 친구목록 중 번호를 불러와서 tolist(), 리스트에 있는 모든 번호에 문자
  friend = pd.read_csv('./file/friend.csv')
  f = friend['phone'].tolist()


  # 버튼에 따른 메시지 설정
  msg = '.'

  if btn_name == 'light_on_btn':
    msg = "불 켜주세요"

  elif btn_name == 'light_off_btn':
    msg = "불 꺼주세요"

  elif btn_name == 'cold_btn':
    msg = "추워요"

  elif btn_name == 'hot_btn':
    msg = "더워요"

  elif btn_name == 'big_btn':
    msg = "대변 하고싶어요"

  elif btn_name == 'small_btn':
    msg = "소변 하고싶어요"

  elif btn_name == 'water_btn':
    msg = "물 주세요"

  elif btn_name == 'out_btn':
    msg = "나가고 싶어요"

  elif btn_name == 'pose_btn':
    msg = '자세가 불편해요'

  elif btn_name == 'emergency_btn':
    msg = '비상호출'

  elif btn_name == 'hungry_btn':
    msg = "배고파요"

  elif btn_name == 'full_btn':
    msg = "배불러요"


  for i in f: # 친구 목록을 읽는 form 문 ~ 82 line
    params = dict()
    params['type'] = 'sms' # Message type ( sms, lms, mms, ata )
    phone = i.replace('-','') # 010-0000-0000 --> 01000000000
    params['to'] = phone # Recipients Number '01000000000,01000000001'
    print(phone)
    params['from'] = '01025914739' # Sender number - 계정에 등록된 번호
    params['text'] = msg # Message

    cool = Message(api_key, api_secret)

    #send 외엔 성공, 실패 여부 체크 없어도됨
    try:
      response = cool.send(params)
      print("Success Count : %s" % response['success_count'])
      print("Error Count : %s" % response['error_count'])
      print("Group ID : %s" % response['group_id'])
      if "error_list" in response:
        print("Error List : %s" % response['error_list'])
    except CoolsmsException as e:
      print("Error Code : %s" % e.code)
      print("Error Message : %s" % e.msg)
