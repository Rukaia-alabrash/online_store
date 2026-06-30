from pydantic import BaseModel
from typing import List, Optional


class SalesDataPoint(BaseModel):
    day: str
    revenue: float
    orders: int
    sales: float


class PerformanceDataPoint(BaseModel):
    month: int
    conversion: float
    traffic: int


class CategoryDataPoint(BaseModel):
    name: str
    value: int
    percentage: str


class Alert(BaseModel):
    id: int
    type: str        # "warning" | "info" | "success"
    message: str
    time: str


class RecentOrder(BaseModel):
    id: int
    createdAt: Optional[str]
    total: float
    status: str


class TopProduct(BaseModel):
    id: int
    name: str
    image: str
    price: float
    sales: int


class DashboardOut(BaseModel):
    # الإحصائيات الرئيسية
    totalRevenue: float
    totalOrders: int
    totalProducts: int
    totalUsers: int

    # نسب التغيّر
    revenueTrend: str
    ordersTrend: str
    productsTrend: str
    usersTrend: str

    # إحصائيات سريعة
    pendingOrders: int
    lowStock: int
    newCustomers: int
    avgOrderValue: float

    # المخططات
    salesData: List[SalesDataPoint]
    performanceData: List[PerformanceDataPoint]
    categoryData: List[CategoryDataPoint]

    # القوائم
    alerts: List[Alert]
    recentOrders: List[RecentOrder]
    topProducts: List[TopProduct]