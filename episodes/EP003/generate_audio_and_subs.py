"""
EP003 — 나레이션 · 자막 · 컷 길이 생성

이 파일은 대본만 들고 있다. 처리는 scripts/lib_narration.py 가 한다.

    python episodes/EP003/generate_audio_and_subs.py
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
        note="도입 훅 - 15세기 유럽 귀족 대연회장과 향신료",
        vo="중세 유럽에서 후추가 금값이었던 건, 고기 맛 때문이 아니었습니다.",
        subs=["중세 유럽에서 후추가 금값이었던 건,", "*고기 맛 때문이 아니었습니다.*"],
    ),
    Beat(
        scene="S02", kind="ai_still", move="dolly_in", pause=0.42,
        note="난관1 - 중세 정육소와 소금에 절인 고기(염장)",
        vo="고기 썩은 내를 가리려 썼다는 말은, 완전히 틀렸습니다.",
        subs=["고기 썩은 내를 가리려 썼다는 말은", "*완전히 틀렸습니다.*"],
    ),
    Beat(
        scene="S03", kind="diagram", pause=0.40,
        note="도해 - 픽토그램 대비 : 통념(썩은고기 방부 ✕) vs 실체(귀족 신선육 소비 ○)",
        vo="신선한 고기를 먹던 귀족만 샀고, 가난한 사람은 구경도 못 했습니다.",
        subs=["신선한 고기를 먹던 귀족만 샀고,", "가난한 사람은 *구경도 못 했습니다.*"],
    ),
    Beat(
        scene="S04", kind="diagram", pause=0.40,
        note="도해 - 인과 화살표 : 다단계 무역로 + 신분재·중세 의학 수요",
        vo="다단계 무역로와 중세 의학, 두 조건이 가격을 밀어 올렸습니다.",
        subs=["다단계 무역로와 중세 의학,", "*두 조건이 가격을 밀어 올렸습니다.*"],
    ),
    Beat(
        scene="S05", kind="ai_hero", move="dolly_in", pause=0.40,
        note="해결1 - 인도양 말라바르(칼리컷) 항구와 무역선 선적",
        vo="첫째, 인도에서 출발해 수십 개 거점을 거치며 관세가 쌓였습니다.",
        subs=["첫째, 인도에서 출발해 수십 개 거점을 거치며", "*관세가 쌓였습니다.*"],
    ),
    Beat(
        scene="S06", kind="diagram", pause=0.44,
        note="도해 - 지도 이동 / 수치 그래프 : 산지(1x) → 관세·마진 → 베네치아 독점(60x 폭등)",
        vo="유럽에 도착하면 산지 가격의 60배로 뛰었지만, 베네치아의 독점이었습니다.",
        subs=["유럽에 도착하면 *산지 가격의 60배*로 뛰었지만,", "베네치아의 *독점*이었습니다."],
    ),
    Beat(
        scene="S07", kind="ai_still", move="dolly_in", pause=0.40,
        note="해결2 - 15세기 유럽 약제상과 사체액설 의학서",
        vo="둘째, 소화를 돕는 필수 약재이자, 부를 과시하는 신분재였습니다.",
        subs=["둘째, 소화를 돕는 *필수 약재*이자", "부를 과시하는 *신분재*였습니다."],
    ),
    Beat(
        scene="S08", kind="ai_hero", move="crane_up", pause=0.42,
        note="요약 - 황혼녘 베네치아 대운하와 산마르코 광장 상인들",
        vo="독점 공급망과 대체 없는 수요가 만나면, 음식은 화폐가 됩니다.",
        subs=["독점 공급망과 대체 없는 수요가 만나면,", "*음식은 화폐가 됩니다.*"],
    ),
    Beat(
        scene="S09", kind="diagram", pause=0.0,
        note="도해 - 인과 요약 + 루프백 (끝 프레임 BG 수렴)",
        vo="그래서 향신료가 비쌌던 진짜 이유는, 맛이 아니라 독점과 신분이었습니다.",
        subs=["그래서 향신료가 비쌌던 진짜 이유는,", "맛이 아니라 *독점과 신분*이었습니다."],
    ),
]

if __name__ == "__main__":
    generate("EP003", BEATS)
