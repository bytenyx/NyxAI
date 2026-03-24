from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="提示信息")

    @classmethod
    def success_response(cls, data: T = None, message: str = None) -> 'ApiResponse[T]':
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(cls, error: str, data: T = None) -> 'ApiResponse[T]':
        return cls(success=False, error=error, data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> 'PaginatedResponse[T]':
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ValidationError(BaseModel):
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")
    details: Optional[List[ValidationError]] = Field(None, description="验证错误详情")