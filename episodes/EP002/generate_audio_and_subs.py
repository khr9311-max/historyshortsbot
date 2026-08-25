"""
EP002 — 나레이션 · 자막 · 컷 길이 생성

이 파일은 대본만 들고 있다. 처리는 scripts/lib_narration.py 가 한다.

    python episodes/EP002/generate_audio_and_subs.py
    → assets/vo/vo.wav · sub.ass · scenes.tsv · timing.json

pause : 이 문장 뒤의 정지 길이(초). 컷 전환이 여기서 일어난다.
subs  : 화면 자막. *별표* 로 감싼 구간이 ACCENT. 한 컷 최대 2줄, 강조는 한 곳만.

바이블 §8  단일 원인 금지 · 학설 구분 명시 · 출처 없는 수치 금지
바이블 §11 마지막 문장은 S01 의 훅으로 이어지게 쓴다 (루프백)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from lib_narration import Beat, generate  # noqa: E402

BEATS = [
    Beat(
        scene="S01", kind="ai_hero", move="orbit", pause=0.42,
        note="도입 훅 - 명나라 황실 은 창고",
        vo="전 세계 은의 3분의 1을 빨아들였던 제국이, 은 때문에 파산했습니다.",
        subs=["전 세계 은의 3분의 1을 빨아들였던 제국이,", "*은 때문에 파산했습니다.*"],
    ),
    Beat(
        scene="S02", kind="ai_still", move="dolly_in", pause=0.44,
        note="난관 - 16세기 명나라 교역 항구",
        vo="16세기 명나라에는 아메리카와 일본의 은이 끝없이 쏟아졌습니다.",
        subs=["16세기 명나라에는 아메리카와 일본의 은이", "*끝없이 쏟아졌습니다.*"],
    ),
    Beat(
        scene="S03", kind="diagram", pause=0.40,
        note="도해 - 픽토그램 대비 : 은 풍요 vs 국고 파산·반란",
        vo="돈이 넘치는데 국고는 비었고, 반란이 터졌습니다. 왜였을까요?",
        subs=["돈이 넘치는데 국고는 비었고 반란이 터졌습니다.", "*왜였을까요?*"],
    ),
    Beat(
        scene="S04", kind="diagram", pause=0.40,
        note="도해 - 인과 화살표 : 조세 은납화 + 공급망 충격",
        vo="조세의 은납화와 공급망 충격, 두 조건이 겹쳤습니다.",
        subs=["조세의 은납화와 공급망 충격,", "*두 조건이 겹쳤습니다.*"],
    ),
    Beat(
        scene="S05", kind="ai_hero", move="dolly_in", pause=0.40,
        note="해결1 - 관아 앞 은 세금 납부",
        vo="첫째, 모든 세금을 은으로만 걷는 일조편법이 농민을 묶었습니다.",
        subs=["첫째, 모든 세금을 *은으로만 걷는 일조편법*이", "농민을 묶었습니다."],
    ),
    Beat(
        scene="S06", kind="diagram", pause=0.44,
        note="도해 - 수치 그래프 : 은값 폭등과 농민 실질 세부담 3배",
        vo="둘째, 은 유입이 줄자 은값이 폭등해 농민의 실질 세금이 세 배로 치솟았습니다.",
        subs=["둘째, 은 유입이 줄자 *은값이 폭등*해", "농민의 실질 세금이 *세 배*로 치솟았습니다."],
    ),
    Beat(
        scene="S07", kind="ai_still", move="dolly_in", pause=0.40,
        note="해결2 - 만리장성 북방 초소와 군대",
        vo="은을 못 구한 농민이 무너지자, 제국은 군대 급여조차 주지 못했죠.",
        subs=["은을 못 구한 농민이 무너지자,", "제국은 *군대 급여조차 주지 못했죠.*"],
    ),
    Beat(
        scene="S08", kind="ai_hero", move="crane_up", pause=0.42,
        note="요약 - 먹구름 낀 자금성 궁궐 실루엣",
        vo="통화 통제력을 잃은 제국은, 공급망이 흔들리면 디플레이션에 빠집니다.",
        subs=["통화 통제력을 잃은 제국은,", "*공급망이 흔들리면 디플레이션에 빠집니다.*"],
    ),
    Beat(
        scene="S09", kind="diagram", pause=0.0,
        note="도해 - 인과 요약 + 루프백 (끝 프레임 BG 수렴)",
        vo="그래서 전 세계 은을 가졌던 제국이, 가장 처참하게 무너졌습니다.",
        subs=["그래서 전 세계 은을 가졌던 제국이,", "가장 *처참하게 무너졌습니다.*"],
    ),
]

if __name__ == "__main__":
    generate("EP002", BEATS)
