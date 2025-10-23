from pathlib import Path

targets = [
    Path("C:/Windows/Fonts/맑은고딕.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
]

found = [str(p) for p in targets if p.exists()]
missing = [str(p) for p in targets if not p.exists()]

print("=== Font Detection ===")
print("Found:", found if found else "없음")
print("Missing:", missing if missing else "없음")

font_env = Path("C:/Windows/Fonts")
print("Fonts directory exists:", font_env.exists())
