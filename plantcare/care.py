from dataclasses import dataclass


@dataclass
class CareGuide:
    light: str
    watering: str
    humidity: str
    notes: str


PLANT_GUIDES = [
    {
        "aliases": ["몬스테라", "monstera"],
        "guide": CareGuide(
            light="밝은 간접광, 직사광은 피하기",
            watering="겉흙 2~3cm가 마르면 흠뻑 주고 배수",
            humidity="중간~높음 (50% 이상 권장)",
            notes="과습에 약함. 통풍 확보, 성장기에는 월 1회 액비가 도움 됩니다.",
        ),
    },
    {
        "aliases": ["스투키", "산세베리아", "snake plant", "sansevieria"],
        "guide": CareGuide(
            light="밝은 곳부터 반그늘까지 적응",
            watering="흙이 완전히 마른 뒤 물주기",
            humidity="낮음~중간",
            notes="겨울철 물주기 간격을 길게 유지하세요. 과습이 가장 큰 실패 원인입니다.",
        ),
    },
    {
        "aliases": ["고무나무", "고무", "ficus elastica", "rubber plant"],
        "guide": CareGuide(
            light="밝은 간접광",
            watering="겉흙이 마르면 충분히 관수",
            humidity="중간",
            notes="잎 먼지를 닦아주면 광합성에 도움 됩니다. 급격한 환경변화는 낙엽 원인입니다.",
        ),
    },
    {
        "aliases": ["알로카시아", "alocasia"],
        "guide": CareGuide(
            light="밝은 간접광",
            watering="흙을 살짝 촉촉하게 유지하되 과습 금지",
            humidity="높음",
            notes="건조하면 잎 끝 마름이 생길 수 있습니다. 가습/자갈 트레이가 효과적입니다.",
        ),
    },
    {
        "aliases": ["자스민", "쟈스민", "재스민", "jasmine"],
        "guide": CareGuide(
            light="밝은 빛, 하루 4~6시간 이상 광량 확보",
            watering="겉흙이 마르면 물주기, 개화기엔 약간 촉촉하게",
            humidity="중간",
            notes="통풍이 중요하며 개화기에는 인산 비율이 높은 비료를 소량 사용하세요.",
        ),
    },
    {
        "aliases": ["제라늄", "geranium", "페라고늄", "pelargonium"],
        "guide": CareGuide(
            light="직사광 포함 밝은 환경 선호",
            watering="흙이 마른 뒤 물주기",
            humidity="낮음~중간",
            notes="잎에 물이 오래 머물지 않게 하고, 꽃대 정리하면 개화 지속에 좋습니다.",
        ),
    },
    {
        "aliases": ["여우꼬리풀", "폭스테일", "foxtail", "asparagus densiflorus"],
        "guide": CareGuide(
            light="밝은 간접광",
            watering="겉흙이 마르면 규칙적으로 물주기",
            humidity="중간~높음",
            notes="건조하면 잎이 쉽게 마릅니다. 분무보다 주변 습도 유지가 효과적입니다.",
        ),
    },
    {
        "aliases": ["달맞이꽃", "낮달맞이꽃", "evening primrose", "oenothera"],
        "guide": CareGuide(
            light="햇빛 좋은 환경",
            watering="과습 피하고 흙이 마르면 물주기",
            humidity="낮음~중간",
            notes="배수가 좋은 토양을 선호합니다. 장마철 과습에 특히 주의하세요.",
        ),
    },
]


def get_care_guide(species: str) -> CareGuide:
    raw = (species or "").strip()
    norm = raw.lower()

    for row in PLANT_GUIDES:
        for alias in row["aliases"]:
            alias_norm = alias.lower()
            if alias_norm in norm or norm in alias_norm:
                return row["guide"]

    return CareGuide(
        light="밝은 간접광을 기본으로 두고 식물 반응에 맞춰 조정",
        watering="겉흙이 마른 뒤 충분히 관수하고 배수 상태 확인",
        humidity="중간 (40~60%)",
        notes="처음 2주간 잎 상태와 흙 마름 속도를 관찰해 주기를 맞추세요.",
    )

