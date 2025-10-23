"""User-provided analysis plan for demo execution."""

from datetime import datetime

USER_ANALYSIS_PLAN = {
    "segments": [
        {
            "name": "산업 게이트웨이",
            "keywords": [
                "industrial edge",
                "factory gateway",
                "predictive maintenance edge",
                "edge plc analytics",
            ],
            "sources": ["IEEE", "Gartner", "Siemens blog"],
            "priority": 3,
        },
        {
            "name": "온디바이스",
            "keywords": [
                "on-device ai",
                "mobile npu",
                "privacy inference",
                "ai wearable",
            ],
            "sources": ["arXiv", "Qualcomm press", "Google AI blog"],
            "priority": 3,
        },
        {
            "name": "차량 엣지",
            "keywords": [
                "vehicle edge",
                "adas compute",
                "autonomous edge ai",
            ],
            "sources": ["SAE", "OEM investor reports", "NHTSA"],
            "priority": 2,
        },
        {
            "name": "통신 인프라",
            "keywords": [
                "telco edge",
                "edge cdn",
                "ran intelligence",
                "5g mec",
            ],
            "sources": ["3GPP", "ETSI", "GSMA"],
            "priority": 2,
        },
    ],
    "time_window": "24m",
    "scenario_targets": {
        "horizon": f"{datetime.now().year + 1}-{datetime.now().year + 5}",
        "scenarios": ["보수", "중립", "가속"],
    },
}
