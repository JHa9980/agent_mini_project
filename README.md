# Edge AI 미래 트렌드 분석 에이전트

Edge AI에 관심 있는 기업 실무자를 위해 향후 5년 트렌드를 진단하고 전략 실행 방향을 제안하는 LangGraph 기반 멀티 에이전트 워크플로입니다.

## Overview

- **목표**: Edge AI 세그먼트별 트렌드 신호를 수집·평가하고 5년 전략 시나리오를 제시하는 보고서를 자동 생성
- **방법**: Tavily 웹 검색 + OpenAI GPT-4o-mini LLM + LangGraph 상태 머신을 활용한 단계별 분석
- **도구**: LangGraph, LangChain, Python 3.11, OpenAI API, Tavily Search, FPDF

## Architecture
<img width="300" height="2100" alt="Mermaid Chart - Create complex, visual diagrams with text -2025-10-23-005834" src="https://github.com/user-attachments/assets/ed0312c7-594a-4a5e-bb35-b1255eb58d23" />

- **기본 흐름**: 사용자 계획 → 정보 수집 → 인사이트 매핑 → 정량 지표 산출 → 시나리오 작성 → **보고서 계획**
- **순차적 보고서 생성**: 계획된 목차에 따라 각 섹션의 내용을 루프(Loop)를 돌며 순차적으로 생성합니다.
- **최종 취합**: 생성된 모든 섹션을 하나로 모아 최종 보고서 파일로 저장합니다.
- **피드백 루프**: MetricScorer → FeedbackHandler → InfoCollector로 증거 보강을 요청하는 피드백 루프를 포함합니다.

## Quick Start

프로젝트를 로컬 환경에서 설정하고 실행하는 방법입니다.

### 1. 프로젝트 복제
```bash
# 이 프로젝트를 이미 다운로드한 경우 이 단계는 건너뜁니다.
git clone <repository-url>
cd agent_mini_project
```

### 2. 가상 환경 생성 및 활성화
Python 3.11+ 버전 사용을 권장합니다.
```bash
# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 필수 라이브러리 설치
`requirements.txt` 파일을 사용하여 필요한 모든 라이브러리를 한 번에 설치합니다.
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
프로젝트 루트 디렉토리(`agent_mini_project/`)에 `.env` 파일을 생성하고, 아래 내용을 복사하여 붙여넣으세요. 각 키는 해당 서비스에서 발급받아 교체해야 합니다.

```env
# .env 파일 예시

# --- 필수 API 키 ---
# OpenAI API 키 (https://platform.openai.com/api-keys)
OPENAI_API_KEY="sk-..."

# Tavily Search API 키 (https://tavily.com/#api)
TAVILY_API_KEY="tvly-..."


# --- (선택) LangSmith 추적 설정 ---
# LangSmith 추적을 사용하려면 아래 변수들의 주석을 해제하고 API 키를 입력하세요.
# (https://smith.langchain.com/)
# LANGCHAIN_TRACING_V2="true"
# LANGCHAIN_API_KEY="ls__..."
# LANGCHAIN_PROJECT="agent_mini_project"
```

### 5. 에이전트 실행
이제 메인 애플리케이션을 실행할 수 있습니다.
```bash
python app.py
```

### 6. 결과 확인
실행이 완료되면 `outputs` 디렉토리에서 결과를 확인할 수 있습니다.
- **보고서**: `outputs/edge_ai_trend_report_YYYYMMDD_HHMMSS.pdf` (또는 `.txt`)

## Agents / Nodes

- **정보수집 노드 (InfoCollector)**: 세그먼트·키워드·출처 계획에 따라 Tavily 검색과 요약을 수행하고 증거를 축적
- **인사이트 노드 (InsightMapper)**: 수집된 증거를 기반으로 세그먼트별 트렌드 요약과 선행 지표를 도출
- **지표 산출 노드 (MetricScorer)**: 연구 활동(0~20), 시장 모멘텀(0~10), 배포 준비도(0~10) 지표를 계산하고 진단 태그를 부여
- **피드백 허브 (FeedbackHandler)**: 진단 태그를 해석해 InfoCollector로 증거 확장/재수집 요청을 전달
- **시나리오 플래너 (ScenarioPlanner)**: 정량 지표를 이용해 5년 보수·중립·가속 시나리오와 내러티브를 생성
- **보고서 계획 노드 (ReportPlanner)**: 생성할 보고서의 전체 목차를 정의하고 생성 루프를 초기화
- **섹션 생성 노드 (GenerateSection)**: 단일 섹션의 내용만 전문적으로 생성
- **최종 보고서 취합 노드 (FinalizeReport)**: 생성된 모든 섹션을 취합하여 최종 보고서 파일로 저장

## State

- `analysis_plan`: 사용자 조사 범위(세그먼트, 키워드, 우선순위, 시나리오 대상)
- `evidence_pool`: 세그먼트별 수집 증거(요약, 출처, 신뢰도, 정량 신호)
- `trend_insights`: InsightMapper가 정리한 세그먼트 인사이트와 선행 지표
- `metric_dashboard`: 연구 활동·시장 모멘텀·배포 준비도 지수
- `diagnostics`: coverage-gap / low-confidence / low-volume 진단 태그 목록
- `pending_feedback`: FeedbackHandler가 발행한 후속 수집 요청
- `scenario_outlook`: 5년 시나리오별 CAGR 값과 가정
- `scenario_analysis`: ScenarioPlanner가 작성한 서술형 분석
- `final_report`: 생성된 모든 섹션의 내용을 취합한 최종 보고서 본문
- `report_path` / `report_error`: 결과 파일 경로와 저장 오류 메시지

## Signal & Metrics

| Signal | 기본값 | 추출 조건 예시 |
|--------|--------|----------------|
| papers | 10 | 논문/연구/발표 키워드 |
| patents | 4 | 특허·출원 언급 |
| investments | 60 | 투자·펀딩·달러 금액 |
| search_index | 55 | 시장/트렌드 검색 지표 |
| deployments | 25 | 도입·출시·롤아웃 언급 |
| latency | 26 | 저지연·응답시간 지표 |

- **연구 활동 지수(0~20)** = 0.6×평균 논문 + 0.4×평균 특허 (원점수를 0.8로 나누어 조정)
- **시장 모멘텀 지수(0~10)** = 0.7×평균 투자 + 0.3×평균 검색 지수 (원점수를 10으로 나누어 조정)
- **배포 준비도 지수(0~10)** = 0.5×평균 배포 사례 + 0.5×(100 - 평균 지연) (원점수를 10으로 나누어 조정)
- **진단 태그 기준**  
  - `coverage-gap`: 신뢰도 ≥ 0.6인 증거가 없는 세그먼트  
  - `low-confidence`: 평균 신뢰도 < 0.5  
  - `low-volume`: 증거 건수 < 2

## Report Structure

1. 요약: 핵심 메시지, 우선 주목 세그먼트, 성장률 하이라이트  
2. 서론: 보고서 목적·범위·데이터 활용 범위  
3. 글로벌 현황: 지난 24개월 시장 규모·투자·정책 흐름 요약  
4. 트렌드 인사이트: 세그먼트별 신호·전조 징후 정리  
5. 5년 시나리오 분석: 보수·중립·가속 시나리오, 촉진/저해 요인, 타임라인  
6. 리스크 및 기회: 공급망, 네트워크, 규제 리스크와 대응 전략  
7. 전략 제언: 투자, 파트너십, 기술 내재화 우선순위  
8. 참고 자료: 사용된 외부 출처 목록  
9. 부록: 정량 지표 표와 진단 태그 요약, 평가 로직 설명

## Directory Structure

`
agent_mini_project/
├── agents/                 # Agent 노드 구현
├── prompts/                # LLM 프롬프트 템플릿
├── tests/                  # 에이전트 단위 테스트 스크립트
├── outputs/                # 보고서 및 그래프 결과
├── .env                    # API 키 및 환경 변수 설정
├── app.py                  # 전체 그래프 실행 스크립트
├── config.py               # 서비스 클라이언트 설정
├── requirements.txt        # Python 라이브러리 종속성
├── state.py                # LangGraph 상태 정의
└── README.md
`
