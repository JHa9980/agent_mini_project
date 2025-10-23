"""LangGraph node for the new sequential report generation architecture."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from fpdf import FPDF  # type: ignore
except ImportError:  # pragma: no cover
    FPDF = None

from config import get_llm
from prompts.report_assembler import SINGLE_SECTION_PROMPT
from state import TrendState

APPENDIX_METRIC_EXPLANATION_MARKDOWN = textwrap.dedent("""
- **연구 활동 지수 (0~20)** = (0.6 × 평균 논문 수 + 0.4 × 평균 특허 수) / 0.8
- **시장 모멘텀 지수 (0~10)** = (0.7 × 평균 투자 금액 + 0.3 × 평균 검색 지수) / 10
- **배포 준비도 지수 (0~10)** = (0.5 × 평균 배포 건수 + 0.5 × (100 - 평균 지연 시간)) / 10
""").strip()

APPENDIX_METRIC_EXPLANATION_PLAIN = textwrap.dedent("""
- 연구 활동 지수(0~20) = (0.6 × 평균 논문 수 + 0.4 × 평균 특허 수) / 0.8
- 시장 모멘텀 지수(0~10) = (0.7 × 평균 투자 금액 + 0.3 × 평균 검색 지수) / 10
- 배포 준비도 지수(0~10) = (0.5 × 평균 배포 건수 + 0.5 × (100 - 평균 지연 시간)) / 10
""").strip()


def report_assembler_node(state: TrendState) -> Dict[str, Any]:
    """Generates content for a single report section."""
    current_section = state["current_section"]
    print(f"--- Generating section: {current_section} ---")

    # Prepare the payload for the LLM
    references = sorted({item.get("source", "출처 미확인") for item in state.get("evidence_pool", [])})

    payload = {
        "section_to_generate": current_section,
        "summary_points": [f"{datetime.now():%Y-%m-%d} 기준 Edge AI 전략 요약"],
        "trend_insights": state.get("trend_insights", []),
        "scenario_outlook": state.get("scenario_outlook"),
        "scenario_analysis": state.get("scenario_analysis"),
        "metric_dashboard": state.get("metric_dashboard", {}),
        "references": references,
        "diagnostics": state.get("diagnostics", []),
        "analysis_plan": state.get("analysis_plan"),
    }

    messages = [
        {"role": "system", "content": SINGLE_SECTION_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    # Invoke the LLM to generate the section content
    try:
        response = get_llm().invoke(messages)
        section_content = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"Error generating section {current_section}: {e}")
        section_content = f"{current_section} 섹션 생성 중 오류가 발생했습니다."

    if "appendix" in current_section.lower() and section_content:
        if "정량 지표 산출" not in section_content:
            appendix_addendum = (
                "\n\n#### 정량 지표 산출 로직\n\n" + APPENDIX_METRIC_EXPLANATION_MARKDOWN
            )
            section_content = section_content.rstrip() + appendix_addendum

    # Update the state with the generated content
    generated_report = state.get("generated_report", {})
    generated_report[current_section] = section_content

    return {"generated_report": generated_report}


def _get_appendix_content() -> str:
    """Generates the appendix content with evaluation logic in Markdown format."""
    return textwrap.dedent(f"""
        ### 부록: 평가 로직 상세

        본 보고서의 정량 분석은 다음과 같은 규칙에 따라 수행되었습니다.

        #### 1. 근거 신뢰 지수 (Evidence Reliability Score) 규칙

        근거 신뢰 지수는 객관성과 일관성을 보장하기 위해 명확한 규칙에 따라 선정됩니다.

        | 출처 유형 | 기본 점수 | 세부 조건 예시 |
        | :--- | :--- | :--- |
        | **학회/전문 보고서** | 0.85 | `arxiv.org`, `acm.org`, `ieee.org` 등 |
        | **주요 통신/경제지** | 0.8 | `reuters.com`, `bloomberg.com`, `wsj.com` 등 |
        | **정부/기관/학교** | 0.75 | `.gov`, `.org`, `.edu` 도메인 |
        | **PDF/리포트 형식** | 0.7 | URL에 `pdf`, `report` 포함 |
        | **주요 기술 매체** | 0.65 | `forbes.com`, `techcrunch.com`, `wired.com` 등 |
        | **일반 뉴스/블로그** | 0.6 | `news`, `blog` 키워드 포함 |
        | **포럼/커뮤니티** | 0.3 | `forum`, `community`, `reddit.com` 등 |

        **가/감점 규칙:**
        - **최신성**: 3개월 이내 데이터 `+0.05`, 1년 이상 경과 데이터 `-0.1`
        - **날짜 정보 부재**: `-0.1`

        #### 2. 정량 지표 산출 로직

        {APPENDIX_METRIC_EXPLANATION_MARKDOWN}

        #### 3. 진단 태그 및 피드백 루프

        결과의 확인 및 부족한 정보 보강을 위해 다음 조건에 해당하면 관련 세그먼트에서 추가 정보를 요구합니다.

        - **`coverage-gap`**: 근거 신뢰 지수 0.6 이상의 증거가 없을 때
        - **`low-confidence`**: 평균 근거 신뢰 지수가 0.5 미만일 때
        - **`low-volume`**: 증거 항목이 2개 미만일 때
    """).strip()


def _get_appendix_content_for_pdf(state: TrendState) -> str:
    """Formats the appendix content with dynamic scores into a simple string suitable for PDF."""
    dashboard = state.get("metric_dashboard", {})

    def format_metric(metric_key: str, name: str, unit: str) -> list[str]:
        metric_data = dashboard.get(metric_key, {})
        scores = metric_data.get("segment_scores", {})
        lines = [f"- {name} ({unit}):"]
        if not scores:
            lines.append("  (사전 생성 건수 없음)")
        else:
            for segment, score in scores.items():
                lines.append(f"  - {segment}: {score}")
        return lines

    lines: list[str] = [
        "부록: 평가 로직 상세",
        "",
        "1. 정량 지표 요약 (산출 결과)",
    ]

    lines.extend(format_metric("research_activity", "연구 활동 지수", "0-20"))
    lines.extend(format_metric("market_reaction", "시장 모멘텀 지수", "0-10"))
    lines.extend(format_metric("deployment_readiness", "배포 준비도 지수", "0-10"))

    lines.extend([
        "",
        "2. 정량 지표 산출 로직",
    ])
    lines.extend(APPENDIX_METRIC_EXPLANATION_PLAIN.splitlines())

    confidence_lines = [
        "",
        "3. 근거 신뢰 지수 (Evidence Reliability Score) 규칙",
        "- 학회/전문 보고서: 0.85점 (예: arxiv.org, acm.org, ieee.org)",
        "- 주요 통신/경제지: 0.8점 (예: reuters.com, bloomberg.com, wsj.com)",
        "- 정부/기관/학교: 0.75점 (예: .gov, .org, .edu 도메인)",
        "- PDF/리포트 형식: 0.7점 (URL에 pdf, report 포함)",
        "- 주요 기술 매체: 0.65점 (예: forbes.com, techcrunch.com, wired.com)",
        "- 일반 뉴스/블로그: 0.6점 (URL에 news, blog 포함)",
        "- 포럼/커뮤니티: 0.3점 (예: forum, community, reddit.com)",
        "- 최신성 보정: 3개월 이내 데이터 +0.05점, 1년 이상 경과 데이터 -0.1점",
        "- 날짜 정보 부재: -0.1점",
    ]
    lines.extend(confidence_lines)

    lines.extend([
        "",
        "4. 진단 태그 및 피드백 루프",
        "- coverage-gap: 근거 신뢰 지수 0.6 이상 증거 미존시 추가 정보 요구",
        "- low-confidence: 평균 근거 신뢰 지수 0.5 미만시 추가 증거 요구",
        "- low-volume: 증거 항목 2개 미만시 보강 요구",
    ])

    return "\n".join(lines)


def save_report_to_file(state: TrendState) -> Dict[str, str]:
    """Saves the final assembled report to a PDF and/or TXT file."""
    report_sections = state.get("report_sections", [])
    generated_report = state.get("generated_report", {})

    # --- Start: Add Title Block ---
    report_title = "Edge AI 기술 트렌드 및 5년 성장 전망 분석 보고서"
    creation_date = f"작성일: {datetime.now():%Y-%m-%d}"
    final_report_text = f"{report_title}\n\n{creation_date}\n\n{'='*50}\n\n"
    # --- End: Add Title Block ---

    # Assemble the final report for TXT (with Markdown appendix)
    for i, section_key in enumerate(report_sections):
        title = f"[{i + 1}. {section_key.upper()}]"
        
        if "부록" in section_key or "appendix" in section_key.lower():
            # For TXT, use the LLM-generated content if available, else fallback
            content = generated_report.get(section_key, _get_appendix_content_for_pdf(state))
        else:
            content = generated_report.get(section_key, f"{section_key} 내용이 생성되지 않았습니다.")
        
        final_report_text += f"{title}\n\n{content}\n\n\n"

    root_dir = Path(__file__).resolve().parent.parent
    outputs_dir = root_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = outputs_dir / f"edge_ai_trend_report_{timestamp}.pdf"
    report_path_str: str
    report_error: Optional[str] = None

    if FPDF is None:
        txt_path = pdf_path.with_suffix(".txt")
        txt_path.write_text(final_report_text, encoding="utf-8")
        report_path_str = str(txt_path)
        report_error = "fpdf 패키지가 설치되지 않아 TXT로 저장했습니다."
    else:
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            _register_korean_font(pdf)

            # --- Add Title Block to PDF ---
            pdf.set_font("MalgunGothic", "B", size=18)
            pdf.cell(0, 10, report_title, ln=True, align='C')
            pdf.set_font("MalgunGothic", "", size=10)
            pdf.cell(0, 10, creation_date, ln=True, align='C')
            pdf.ln(15) # Space after title

            # --- Loop through sections for PDF generation ---
            for i, section_key in enumerate(report_sections):
                title = f"[{i + 1}. {section_key.upper()}]"
                
                # For Appendix, use the PDF-friendly plain text version with dynamic scores
                if "부록" in section_key or "appendix" in section_key.lower():
                    content = _get_appendix_content_for_pdf(state)
                else:
                    content = generated_report.get(section_key, "")

                pdf.set_font("MalgunGothic", "B", size=12)
                pdf.cell(0, 8, title, ln=True)
                pdf.set_font("MalgunGothic", size=11)

                for line in content.splitlines():
                    pdf.multi_cell(0, 6, line)

                pdf.ln(10) # Add space between sections

            pdf.output(str(pdf_path))
            report_path_str = str(pdf_path)

        except Exception as exc:
            txt_path = pdf_path.with_suffix(".txt")
            txt_path.write_text(final_report_text, encoding="utf-8")
            report_path_str = str(txt_path)
            report_error = f"PDF 생성 중 오류 발생: {exc}"

    result = {
        "final_report": final_report_text,
        "report_path": report_path_str,
    }

    if report_error:
        result["report_error"] = report_error

    return result



def _register_korean_font(pdf: FPDF) -> None:
    """Finds and registers a Korean font for FPDF."""
    regular_candidates = [
        Path("C:/Windows/Fonts/맑은 고딕.ttf"),
        Path("C:/Windows/Fonts/malgun.ttf"),
    ]
    bold_candidates = [
        Path("C:/Windows/Fonts/맑은 고딕 Bold.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
    ]

    regular_font = next((p for p in regular_candidates if p.exists()), None)
    bold_font = next((p for p in bold_candidates if p.exists()), None)

    if not regular_font:
        raise FileNotFoundError("맑은 고딕(malgun) 폰트를 찾을 수 없습니다. Windows 폰트 설치를 확인해 주세요.")

    pdf.add_font("MalgunGothic", "", str(regular_font), uni=True)
    if bold_font:
        pdf.add_font("MalgunGothic", "B", str(bold_font), uni=True)
    else:
        # Fallback for bold if not found
        pdf.add_font("MalgunGothic", "B", str(regular_font), uni=True)
