from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from app.models.receipt import Receipt, ReceiptStatus
from app.models.product import Product
from app.models.user import User
from app.models.order_item import OrderItem
from app.models.product_translation import ProductTranslation
from app.models.product_image import ProductImage
from app.models.category import Category


LOW_STOCK_THRESHOLD = 10
NEW_CUSTOMER_DAYS = 30


def _trend(current: float, previous: float) -> str:
    """تحويل الأرقام إلى نسبة تغيّر مثل '+12.5%' أو '-3.4%'"""
    if previous == 0:
        return "+100.0%" if current > 0 else "0.0%"
    pct = ((current - previous) / previous) * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def _range_bounds(range_: str) -> tuple[datetime, datetime, datetime]:
    """
    يُرجع (period_start, now, prev_start)
    بناءً على النطاق المطلوب: week | month | year
    """
    now = datetime.now(timezone.utc)
    if range_ == "week":
        period_start = now - timedelta(days=7)
        prev_start   = now - timedelta(days=14)
    elif range_ == "month":
        period_start = now - timedelta(days=30)
        prev_start   = now - timedelta(days=60)
    else:  # year
        period_start = now - timedelta(days=365)
        prev_start   = now - timedelta(days=730)

    return period_start, now, prev_start


# ── دوال الإحصائيات الرئيسية ──────────────────────────────────────────────────

def _revenue(db: Session, since: datetime = None, until: datetime = None) -> float:
    """مجموع الإيرادات للطلبات المكتملة أو المؤكدة فقط"""
    q = db.query(func.coalesce(func.sum(Receipt.total_price), 0)).filter(
        Receipt.status.in_([ReceiptStatus.DELIVERED, ReceiptStatus.CONFIRMED])
    )
    if since:
        q = q.filter(Receipt.created_at >= since)
    if until:
        q = q.filter(Receipt.created_at < until)
    return float(q.scalar())


def _order_count(db: Session, since: datetime = None, until: datetime = None) -> int:
    q = db.query(func.count(Receipt.id))
    if since:
        q = q.filter(Receipt.created_at >= since)
    if until:
        q = q.filter(Receipt.created_at < until)
    return q.scalar()


def _product_count(db: Session, since: datetime = None, until: datetime = None) -> int:
    q = db.query(func.count(Product.id))
    if since:
        q = q.filter(Product.created_at >= since)
    if until:
        q = q.filter(Product.created_at < until)
    return q.scalar()


def _user_count(db: Session, since: datetime = None, until: datetime = None) -> int:
    q = db.query(func.count(User.id))
    if since:
        q = q.filter(User.created_at >= since)
    if until:
        q = q.filter(User.created_at < until)
    return q.scalar()


# ── مخطط المبيعات ─────────────────────────────────────────────────────────────

def _sales_data(db: Session, range_: str) -> list:
    """
    تجميع الإيرادات وعدد الطلبات لكل يوم أو شهر
    باستخدام date_trunc من PostgreSQL للتجميع الفعّال
    """
    period_start, now, _ = _range_bounds(range_)
    trunc_unit = "day" if range_ in ("week", "month") else "month"

    rows = (
        db.query(
            func.date_trunc(trunc_unit, Receipt.created_at).label("bucket"),
            func.sum(Receipt.total_price).label("revenue"),
            func.count(Receipt.id).label("orders"),
        )
        .filter(Receipt.created_at >= period_start)
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    result = []
    for row in rows:
        bucket: datetime = row.bucket
        label = bucket.strftime("%a") if trunc_unit == "day" else bucket.strftime("%b")
        revenue = float(row.revenue or 0)
        result.append({
            "day": label,
            "revenue": revenue,
            "orders": row.orders,
            # تقدير مبدئي — استبدله بحساب حقيقي عند توفّر بيانات التكلفة
            "sales": revenue * 0.75,
        })
    return result


# ── مخطط الأداء ───────────────────────────────────────────────────────────────

def _performance_data(db: Session) -> list:
    """
    عدد الطلبات الشهرية للـ 12 شهراً الماضية كمؤشر للحركة.
    نسبة التحويل = (الطلبات المُسلَّمة / إجمالي الطلبات) × 100 لكل شهر.
    """
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)

    rows = (
        db.query(
            func.date_trunc("month", Receipt.created_at).label("month"),
            func.count(Receipt.id).label("total"),
            func.sum(
                case((Receipt.status == ReceiptStatus.DELIVERED, 1), else_=0)
            ).label("delivered"),
        )
        .filter(Receipt.created_at >= twelve_months_ago)
        .group_by("month")
        .order_by("month")
        .all()
    )

    result = []
    for row in rows:
        total = row.total or 1  # تجنّب القسمة على صفر
        conversion = round((row.delivered / total) * 100, 1)
        result.append({
            "month": row.month.month,
            "conversion": conversion,
            # تقدير مبدئي — استبدله ببيانات حركة حقيقية لاحقاً
            "traffic": row.total * 100,
        })
    return result


# ── توزيع الفئات ──────────────────────────────────────────────────────────────

def _category_data(db: Session, lang: str = "en") -> list:
    """
    عدد المنتجات لكل فئة بحسب اللغة المطلوبة، مع نسبة كل فئة من الإجمالي.
    يتم تطبيع الأسماء (lower + strip) لدمج الفئات المتطابقة بصرف النظر
    عن حالة الأحرف، مثل "Sports" و "sports".
    """
    rows = (
        db.query(
            func.lower(func.trim(Category.name)).label("name_key"),
            func.count(ProductTranslation.product_id).label("value"),
        )
        .join(ProductTranslation, ProductTranslation.category_id == Category.id)
        .filter(Category.lang_code == lang)
        .group_by("name_key")
        .all()
    )

    total = sum(row.value for row in rows)
    if total == 0:
        return []

    return [
        {
            "name": row.name_key.capitalize(),
            "value": row.value,
            "percentage": f"{round((row.value / total) * 100)}%",
        }
        for row in rows
    ]

# ── أفضل المنتجات مبيعاً ──────────────────────────────────────────────────────

def _top_products(db: Session, lang: str = "en", limit: int = 5) -> list:
    """
    المنتجات مرتبةً حسب إجمالي الوحدات المباعة.
    استعلام تجميعي واحد + استعلامان bulk — بدون أي N+1.
    """
    rows = (
        db.query(
            Product.id,
            Product.price,
            func.sum(OrderItem.quantity).label("sales"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.price)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )

    if not rows:
        return []

    product_ids = [r.id for r in rows]
    sales_map   = {r.id: int(r.sales) for r in rows}
    price_map   = {r.id: r.price for r in rows}

    # جلب الأسماء والصور بـ bulk query واحد لكل منهما — بدون N+1
    translations = (
        db.query(ProductTranslation)
        .filter(
            ProductTranslation.product_id.in_(product_ids),
            ProductTranslation.lang_code == lang,
        )
        .all()
    )
    name_map = {t.product_id: t.name for t in translations}

    images = (
        db.query(ProductImage)
        .filter(
            ProductImage.product_id.in_(product_ids),
            ProductImage.is_primary == True,
        )
        .all()
    )
    image_map = {img.product_id: img.url for img in images}

    # الحفاظ على ترتيب المبيعات
    return [
        {
            "id": pid,
            "name":  name_map.get(pid, ""),
            "image": image_map.get(pid, ""),
            "price": price_map.get(pid, 0.0),
            "sales": sales_map[pid],
        }
        for pid in product_ids
    ]


# ── آخر الطلبات ───────────────────────────────────────────────────────────────

def _recent_orders(db: Session, limit: int = 5) -> list:
    receipts = (
        db.query(Receipt)
        .order_by(Receipt.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "total":  float(r.total_price),
            "status": r.status.value if hasattr(r.status, "value") else r.status,
        }
        for r in receipts
    ]


# ── التنبيهات (محسوبة من البيانات الفعلية) ───────────────────────────────────

def _alerts(db: Session) -> list:
    alerts = []
    alert_id = 1

    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.stock <= LOW_STOCK_THRESHOLD, Product.stock > 0)
        .scalar()
    )
    if low_stock_count:
        alerts.append({
            "id": alert_id, "type": "warning",
            "message": f"Low stock for {low_stock_count} products",
            "time": "just now",
        })
        alert_id += 1

    new_users_today = (
        db.query(func.count(User.id))
        .filter(User.created_at >= datetime.now(timezone.utc) - timedelta(hours=24))
        .scalar()
    )
    if new_users_today:
        alerts.append({
            "id": alert_id, "type": "info",
            "message": f"{new_users_today} new user(s) signed up today",
            "time": "today",
        })
        alert_id += 1

    recent_delivered = (
        db.query(func.count(Receipt.id))
        .filter(
            Receipt.status == ReceiptStatus.DELIVERED,
            Receipt.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
        )
        .scalar()
    )
    if recent_delivered:
        alerts.append({
            "id": alert_id, "type": "success",
            "message": f"{recent_delivered} order(s) delivered today",
            "time": "today",
        })

    return alerts


# ── الدالة الرئيسية ───────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session, range_: str = "week", lang: str = "en") -> dict:
    period_start, now, prev_start = _range_bounds(range_)

    # الفترة الحالية
    cur_revenue  = _revenue(db, since=period_start, until=now)
    cur_orders   = _order_count(db, since=period_start, until=now)
    cur_products = _product_count(db, since=period_start, until=now)
    cur_users    = _user_count(db, since=period_start, until=now)

    # الفترة السابقة (نافذة منفصلة تماماً — ضرورية لدقة نسب التغيّر)
    prev_revenue  = _revenue(db, since=prev_start, until=period_start)
    prev_orders   = _order_count(db, since=prev_start, until=period_start)
    prev_products = _product_count(db, since=prev_start, until=period_start)
    prev_users    = _user_count(db, since=prev_start, until=period_start)

    # الإجماليات الكلية لبطاقات الإحصاء
    total_revenue  = _revenue(db)
    total_orders   = _order_count(db)
    total_products = _product_count(db)
    total_users    = _user_count(db)

    pending_orders = (
        db.query(func.count(Receipt.id))
        .filter(Receipt.status == ReceiptStatus.PENDING)
        .scalar()
    )
    low_stock = (
        db.query(func.count(Product.id))
        .filter(Product.stock <= LOW_STOCK_THRESHOLD)
        .scalar()
    )
    new_customers = (
        db.query(func.count(User.id))
        .filter(User.created_at >= datetime.now(timezone.utc) - timedelta(days=NEW_CUSTOMER_DAYS))
        .scalar()
    )
    avg_order_value = float(
        db.query(func.coalesce(func.avg(Receipt.total_price), 0)).scalar()
    )

    return {
        "totalRevenue":  total_revenue,
        "totalOrders":   total_orders,
        "totalProducts": total_products,
        "totalUsers":    total_users,

        "revenueTrend":  _trend(cur_revenue,  prev_revenue),
        "ordersTrend":   _trend(cur_orders,   prev_orders),
        "productsTrend": _trend(cur_products, prev_products),
        "usersTrend":    _trend(cur_users,    prev_users),

        "pendingOrders": pending_orders,
        "lowStock":      low_stock,
        "newCustomers":  new_customers,
        "avgOrderValue": avg_order_value,

        "salesData":       _sales_data(db, range_),
        "performanceData": _performance_data(db),
        "categoryData":    _category_data(db, lang),

        "alerts":       _alerts(db),
        "recentOrders": _recent_orders(db),
        "topProducts":  _top_products(db, lang),
    }