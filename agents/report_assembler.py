"""LangGraph node for the new sequential report generation architecture."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from fpdf import FPDF  # type: ignore
except ImportError:  # pragma: no cover
    FPDF = None

from config import get_llm
from prompts.report_assembler import SINGLE_SECTION_PROMPT
from state import TrendState


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

    # Update the state with the generated content
    generated_report = state.get("generated_report", {})
    generated_report[current_section] = section_content

    return {"generated_report": generated_report}


def save_report_to_file(state: TrendState) -> Dict[str, str]:
    """Saves the final assembled report to a PDF and/or TXT file."""
    report_sections = state.get("report_sections", [])
    generated_report = state.get("generated_report", {})

    # --- Start: Add Title Block ---
    report_title = "Edge AI 기술 트렌드 및 5년 성장 전망 분석 보고서"
    creation_date = f"작성일: {datetime.now():%Y-%m-%d}"
    final_report_text = f"{report_title}\n\n{creation_date}\n\n{'='*50}\n\n"
    # --- End: Add Title Block ---

    # Assemble the final report from generated sections
    for i, section_key in enumerate(report_sections):
        title = f"[{i + 1}. {section_key.upper()}]"
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

            # --- Loop through sections ---
            for i, section_key in enumerate(report_sections):
                title = f"[{i + 1}. {section_key.upper()}]"
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