"""
1688 选品品类配置
15 个品类的搜索关键词、价格区间、起订量、回头率门槛
"""

from dataclasses import dataclass, field
from urllib.parse import quote


@dataclass
class Category:
    """单个品类配置"""
    id: int
    name: str
    group: str
    search_keyword: str
    price_min: float
    price_max: float
    price_unit: str
    min_order_low: int
    min_order_high: int
    min_order_unit: str
    repurchase_rate_threshold: float
    category_path: str
    extra_keywords: list[str] = field(default_factory=list)

    @property
    def search_url(self) -> str:
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={quote(self.search_keyword, encoding='gbk')}"


CATEGORIES: list[Category] = [
    # ===== 美妆工具/个护小物件 =====
    Category(
        id=1, name="粉扑/美妆蛋", group="美妆工具/个护",
        search_keyword="粉扑 不吃粉 组合装",
        price_min=2, price_max=8, price_unit="个",
        min_order_low=20, min_order_high=50, min_order_unit="个",
        repurchase_rate_threshold=20.0,
        category_path="美容护肤/彩妆 → 化妆工具 → 粉扑/美妆蛋",
        extra_keywords=["美妆蛋 非乳胶", "气垫粉扑 抗菌", "粉扑 组合装"],
    ),
    Category(
        id=2, name="双眼皮贴", group="美妆工具/个护",
        search_keyword="双眼皮贴 蕾丝 防水",
        price_min=1, price_max=5, price_unit="包",
        min_order_low=50, min_order_high=100, min_order_unit="包",
        repurchase_rate_threshold=15.0,
        category_path="美容护肤/彩妆 → 化妆工具 → 双眼皮贴/双眼皮胶水",
        extra_keywords=["双眼皮贴 雾面隐形", "双眼皮胶水 敏感肌"],
    ),
    Category(
        id=3, name="假睫毛", group="美妆工具/个护",
        search_keyword="假睫毛 分段式 自然款",
        price_min=3, price_max=10, price_unit="盒",
        min_order_low=50, min_order_high=100, min_order_unit="盒",
        repurchase_rate_threshold=25.0,
        category_path="美容护肤/彩妆 → 化妆工具 → 假睫毛",
        extra_keywords=["单簇假睫毛", "嫁接睫毛 朵毛", "鱼尾款假睫毛"],
    ),
    Category(
        id=4, name="美甲贴纸", group="美妆工具/个护",
        search_keyword="美甲贴纸 日韩风",
        price_min=1, price_max=5, price_unit="张",
        min_order_low=100, min_order_high=500, min_order_unit="张",
        repurchase_rate_threshold=15.0,
        category_path="美容护肤/彩妆 → 美甲工具 → 美甲贴纸/贴片",
        extra_keywords=["美甲贴纸 极简", "美甲贴片 穿戴甲", "美甲贴纸 防水"],
    ),
    Category(
        id=5, name="化妆刷套装", group="美妆工具/个护",
        search_keyword="化妆刷 便携 马卡龙",
        price_min=10, price_max=30, price_unit="套",
        min_order_low=30, min_order_high=100, min_order_unit="套",
        repurchase_rate_threshold=20.0,
        category_path="美容护肤/彩妆 → 化妆工具 → 化妆刷",
        extra_keywords=["迷你化妆刷", "化妆刷 透明亚克力", "伸缩化妆刷"],
    ),
    Category(
        id=6, name="修眉套装", group="美妆工具/个护",
        search_keyword="修眉套装 不锈钢",
        price_min=5, price_max=15, price_unit="套",
        min_order_low=50, min_order_high=200, min_order_unit="套",
        repurchase_rate_threshold=15.0,
        category_path="美容护肤/彩妆 → 化妆工具 → 修眉工具",
        extra_keywords=["镊子 医用级", "修眉刀 防刮伤", "眉卡 画眉神器"],
    ),
    Category(
        id=7, name="洗脸巾", group="美妆工具/个护",
        search_keyword="洗脸巾 珍珠纹 加厚",
        price_min=3, price_max=8, price_unit="包",
        min_order_low=100, min_order_high=500, min_order_unit="包",
        repurchase_rate_threshold=20.0,
        category_path="个护/家清 → 纸品/湿巾 → 洗脸巾",
        extra_keywords=["一次性洗脸巾 无荧光剂", "棉柔巾 干湿两用", "洗脸巾 卷筒式"],
    ),
    # ===== 女性饰品 =====
    Category(
        id=8, name="耳环/耳夹", group="女性饰品",
        search_keyword="耳夹 无痛 钛钢",
        price_min=3, price_max=15, price_unit="对",
        min_order_low=20, min_order_high=100, min_order_unit="对",
        repurchase_rate_threshold=25.0,
        category_path="饰品 → 耳饰 → 耳环/耳夹",
        extra_keywords=["耳夹 透明树脂", "耳环 螺旋可调节", "耳环 极简几何"],
    ),
    Category(
        id=9, name="鲨鱼夹/发饰", group="女性饰品",
        search_keyword="鲨鱼夹 大号 绸缎",
        price_min=3, price_max=12, price_unit="个",
        min_order_low=30, min_order_high=100, min_order_unit="个",
        repurchase_rate_threshold=20.0,
        category_path="饰品 → 发饰 → 发圈/抓夹",
        extra_keywords=["大肠圈 绸缎", "抓夹 丝绒", "发夹 不扯头发"],
    ),
    Category(
        id=10, name="项链", group="女性饰品",
        search_keyword="锁骨链 钛钢 不掉色",
        price_min=8, price_max=25, price_unit="条",
        min_order_low=20, min_order_high=50, min_order_unit="条",
        repurchase_rate_threshold=20.0,
        category_path="饰品 → 项链 → 锁骨链",
        extra_keywords=["极简项链 细链", "字母项链 定制", "叠戴项链 套装"],
    ),
    Category(
        id=11, name="开口戒指", group="女性饰品",
        search_keyword="戒指 开口可调节 套装",
        price_min=2, price_max=10, price_unit="个",
        min_order_low=50, min_order_high=200, min_order_unit="个",
        repurchase_rate_threshold=20.0,
        category_path="饰品 → 戒指 → 开口戒指",
        extra_keywords=["开口戒指 复古", "极简戒指 细圈", "情侣戒指 开口"],
    ),
    Category(
        id=12, name="手链/红绳", group="女性饰品",
        search_keyword="红绳手链 本命年",
        price_min=3, price_max=12, price_unit="条",
        min_order_low=30, min_order_high=100, min_order_unit="条",
        repurchase_rate_threshold=15.0,
        category_path="饰品 → 手链 → 红绳/编织手链",
        extra_keywords=["编织手绳 可调节", "手链 转运珠", "情侣红绳"],
    ),
    Category(
        id=13, name="手机链", group="女性饰品",
        search_keyword="手机链 编织 串珠",
        price_min=3, price_max=15, price_unit="条",
        min_order_low=20, min_order_high=100, min_order_unit="条",
        repurchase_rate_threshold=15.0,
        category_path="饰品 → 手机饰品 → 手机链/挂绳",
        extra_keywords=["手机手腕带", "手机链 跨境", "韩国手机链"],
    ),
    Category(
        id=14, name="小方巾", group="女性饰品",
        search_keyword="小方巾 丝光 发带",
        price_min=3, price_max=12, price_unit="条",
        min_order_low=50, min_order_high=200, min_order_unit="条",
        repurchase_rate_threshold=15.0,
        category_path="服饰 → 丝巾/围巾 → 小方巾",
        extra_keywords=["发带 丝巾", "丝巾 双面花色", "复古小方巾"],
    ),
    Category(
        id=15, name="胸针", group="女性饰品",
        search_keyword="胸针 可爱动物",
        price_min=2, price_max=8, price_unit="个",
        min_order_low=50, min_order_high=200, min_order_unit="个",
        repurchase_rate_threshold=15.0,
        category_path="饰品 → 胸针 → 胸针/别针",
        extra_keywords=["胸针 珍珠款", "别针 简约字母", "大衣胸针"],
    ),
]
