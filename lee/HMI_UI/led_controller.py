"""
led_controller.py — 차량 LED 상태 표시 (RC Team 3)

⚠️ 이 스크립트는 노트북이 아니라 오토카 본체(SODA 보드)에서 직접 실행해야 한다.
pop.Pilot으로 LED PWM 채널을 직접 제어하기 때문에, 차량에 연결된 Jupyter
Notebook(또는 SSH 세션) 안에서 돌려야 동작한다.

MQTT 브로커에 붙어서 '이 차량 자신의' event 토픽만 구독하고,
event_type에 따라 확인된 LED 채널을 점멸시킨다.
(전체 차량 event를 구독하는 voice_alert.py와 달리, LED는 자기 차량 것만 반응해야 함)

채널 매핑 (lee/LED/E_LED_test, L_LED_test, R_LED_test 에서 실측 확인됨):
- 왼쪽 방향지시등: 1, 3
- 오른쪽 방향지시등: 0, 2
- 비상등(양쪽 동시): 0, 1, 2, 3
- 브레이크등: 아직 미확정 (4~7번 채널 중 하나로 추정)
  → lee/LED/break_LED_test 로 L/R 테스트 때처럼 한 채널씩 켜보면서 실측 후,
    아래 BRAKE_CHANNELS 리스트만 채우면 됨. 그 전까진 안전하게 무시된다.
"""

import json
import threading
import time

import paho.mqtt.client as mqtt
from pop import Pilot

# ── 설정 ──────────────────────────────────────────────────────────
BROKER_ADDRESS = "172.20.10.5"
PORT = 1883
CAR_ID = "A"  # ⚠️ 보드마다 실행 전에 반드시 A/B/C 중 이 차량 값으로 맞출 것
EVENT_TOPIC = f"rcteam3/autocar/{CAR_ID}/event"

LEFT_CHANNELS = [1, 3]
RIGHT_CHANNELS = [0, 2]
HAZARD_CHANNELS = [0, 1, 2, 3]
BRAKE_CHANNELS = []  # TODO: break_LED_test로 실측 후 채널 번호 채우기

LED = Pilot.PWM(1, 0x5c)
LED.setFreq(50)

_blink_lock = threading.Lock()
_blink_token = 0  # 새 이벤트가 오면 이전 점멸 스레드를 중단시키기 위한 토큰


def _all_off():
    for ch in range(8):
        LED.setDuty(ch, 0)


def _blink(channels, times: int, interval: float):
    """channels를 times번 점멸한다. 도중에 새 이벤트가 오면 즉시 중단됨."""
    if not channels:
        print("⚠️ 아직 채널이 확정되지 않은 LED 이벤트 — 무시")
        return

    global _blink_token
    with _blink_lock:
        _blink_token += 1
        my_token = _blink_token

    for _ in range(times):
        if my_token != _blink_token:
            return  # 새 이벤트가 끼어들었으니 이 점멸은 중단
        for ch in channels:
            LED.setDuty(ch, 99)
        time.sleep(interval)
        for ch in channels:
            LED.setDuty(ch, 0)
        time.sleep(interval)


def trigger(event_type: str, detail: dict):
    if event_type == "lane_change":
        direction = detail.get("direction")
        if direction == "left":
            threading.Thread(target=_blink, args=(LEFT_CHANNELS, 5, 0.2), daemon=True).start()
        elif direction == "right":
            threading.Thread(target=_blink, args=(RIGHT_CHANNELS, 5, 0.2), daemon=True).start()
    elif event_type == "emergency_stop":
        threading.Thread(target=_blink, args=(HAZARD_CHANNELS, 15, 0.3), daemon=True).start()
    elif event_type == "brake":
        threading.Thread(target=_blink, args=(BRAKE_CHANNELS, 3, 0.15), daemon=True).start()
    # obstacle_detected는 LED 반응 없음 (TTS 전용)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ [LED 시스템] 브로커에 연결되었습니다! ({CAR_ID} 차량, {EVENT_TOPIC} 구독)")
        client.subscribe(EVENT_TOPIC)
    else:
        print(f"❌ 연결 실패! 코드: {rc}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"⚠️ JSON 파싱 실패: {msg.payload!r}")
        return

    event_type = data.get("event_type")
    detail = data.get("detail", {})
    trigger(event_type, detail)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER_ADDRESS, PORT, 60)
    print(f"🚦 [LED 시스템] {CAR_ID} 차량 LED 컨트롤러 시작...")
    client.loop_forever()
except (KeyboardInterrupt, SystemExit):
    print("\n🛑 LED 컨트롤러를 종료합니다.")
finally:
    _all_off()
