# 🚗 Rc_team3: 엣지 AI 기반 AutoCar Prime 군집 자율주행

본 프로젝트는 GPU 기반 엣지 슈퍼컴퓨터가 탑재된 AutoCar Prime 3대를 활용하여, V2V(Vehicle-to-Vehicle) 통신 기반의 군집주행(Platooning) 및 웹 관제 시스템을 구축하는 프로젝트입니다.

## 📂 디렉토리 구조 및 역할 분담 (Monorepo)

전체 시스템은 마이크로 아키텍처 패턴을 따르며, 3개의 독립적인 코어 프로세스와 이를 통합 실행하는 스크립트로 구성됩니다.

```text
Rc_team3/
├── .gitignore                 # GitHub에 올리지 않을 파일 설정 (가중치 파일, 로그 등)
├── README.md                  # 프로젝트 설명, 팀원 역할, 실행 가이드 작성
├── start_system.sh            # 각 모듈을 동시에 실행하기 위한 메인 스크립트 (tmux)
│
├── AI_Core/                   # [주영찬 & 박재혁] 주행 제어 및 비전 AI
│   ├── motor_test.py          # 기초 모터 구동 테스트 
│   ├── line_tracer.py         # 선두 차량(A) 카메라 비전 및 차선 유지 로직
│   ├── platoon_follower.py    # 후미 차량(B, C) YOLO 객체 추종 및 PID 제어 로직
│   └── models/                # 학습된 딥러닝 모델 파일 보관 폴더 (.pt 등)
│
├── HMI_UI/                    # [이명연] 하드웨어 시각화 및 음성 피드백
│   ├── led_controller.py      # 비상 점멸등(비깜) 및 브레이크등 제어 로직
│   └── voice_alert.py         # 텍스트를 음성으로 변환(TTS)하여 출력하는 로직
│
└── Backend_Dash/              # [권신용] 인프라, 통신 및 통합 관제 대시보드
    ├── dummy_publisher.py     # 가짜 센서 데이터를 쏘아주는 테스트용 스크립트
    ├── backend/               
    │   ├── main.py            # FastAPI 서버 실행 
    │   └── mqtt_broker.py     # 차량 간 통신을 위한 MQTT 브로커 세팅
    └── frontend/              
        ├── src/               # React 컴포넌트 (차량 상태표, 카메라 피드 등)
        └── package.json       # 프론트엔드 의존성 관리
