"""
CRUD operations for metrics and raw data models
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.crud.base import CRUDBase
from app.models.metrics import TokenMetrics, TokenScores
from app.models.raw_data import BirdeyeRawData


class CRUDTokenMetrics(CRUDBase[TokenMetrics, dict, dict]):
    """
    CRUD операции для метрик токенов
    """

    def get_by_token(
        self, 
        db: Session, 
        *, 
        token_id: UUID,
        hours_back: int = 24,
        limit: int = 1000
    ) -> List[TokenMetrics]:
        """
        Получить метрики токена за указанный период
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        return (
            db.query(TokenMetrics)
            .filter(
                and_(
                    TokenMetrics.token_id == token_id,
                    TokenMetrics.timestamp >= cutoff_time
                )
            )
            .order_by(desc(TokenMetrics.timestamp))
            .limit(limit)
            .all()
        )

    def get_latest(self, db: Session, *, token_id: UUID) -> Optional[TokenMetrics]:
        """
        Получить последние метрики токена
        """
        return (
            db.query(TokenMetrics)
            .filter(TokenMetrics.token_id == token_id)
            .order_by(desc(TokenMetrics.timestamp))
            .first()
        )

    def get_metrics_summary(
        self, 
        db: Session, 
        *, 
        token_id: UUID,
        hours_back: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Получить сводку метрик за период
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        metrics = (
            db.query(TokenMetrics)
            .filter(
                and_(
                    TokenMetrics.token_id == token_id,
                    TokenMetrics.timestamp >= cutoff_time
                )
            )
            .order_by(desc(TokenMetrics.timestamp))
            .all()
        )
        
        if not metrics:
            return None
        
        # Агрегируем данные
        total_tx_5m = sum(m.tx_count_5m for m in metrics)
        total_volume_5m = sum(float(m.volume_5m_usd) for m in metrics)
        avg_liquidity = sum(float(m.liquidity_usd) for m in metrics) / len(metrics)
        latest_holders = metrics[0].holders_count if metrics else 0
        
        return {
            "token_id": str(token_id),
            "period_hours": hours_back,
            "data_points": len(metrics),
            "total_transactions_5m": total_tx_5m,
            "total_volume_5m_usd": total_volume_5m,
            "average_liquidity_usd": avg_liquidity,
            "latest_holders_count": latest_holders,
            "first_timestamp": metrics[-1].timestamp if metrics else None,
            "last_timestamp": metrics[0].timestamp if metrics else None
        }

    def cleanup_old_metrics(self, db: Session, *, days_to_keep: int = 30) -> int:
        """
        Очистка старых метрик
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = (
            db.query(TokenMetrics)
            .filter(TokenMetrics.timestamp < cutoff_date)
            .delete()
        )
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old metric records")
        return deleted_count


class CRUDTokenScores(CRUDBase[TokenScores, dict, dict]):
    """
    CRUD операции для скоров токенов
    """

    def get_by_token(
        self, 
        db: Session, 
        *, 
        token_id: UUID,
        model_name: Optional[str] = None,
        hours_back: int = 24,
        limit: int = 1000
    ) -> List[TokenScores]:
        """
        Получить скоры токена
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        query = db.query(TokenScores).filter(
            and_(
                TokenScores.token_id == token_id,
                TokenScores.calculated_at >= cutoff_time
            )
        )
        
        if model_name:
            query = query.filter(TokenScores.model_name == model_name)
        
        return (
            query
            .order_by(desc(TokenScores.calculated_at))
            .limit(limit)
            .all()
        )

    def get_latest_score(
        self, 
        db: Session, 
        *, 
        token_id: UUID,
        model_name: str
    ) -> Optional[TokenScores]:
        """
        Получить последний скор токена для указанной модели
        """
        return (
            db.query(TokenScores)
            .filter(
                and_(
                    TokenScores.token_id == token_id,
                    TokenScores.model_name == model_name
                )
            )
            .order_by(desc(TokenScores.calculated_at))
            .first()
        )

    def get_top_tokens(
        self,
        db: Session,
        *,
        model_name: str,
        min_score: float = 0.0,
        limit: int = 10,
        hours_back: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Получить топ токены по скору
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Получаем последние скоры для каждого токена
        scores = (
            db.query(TokenScores)
            .filter(
                and_(
                    TokenScores.model_name == model_name,
                    TokenScores.score_value >= min_score,
                    TokenScores.calculated_at >= cutoff_time
                )
            )
            .order_by(desc(TokenScores.calculated_at))
            .all()
        )
        
        # Группируем по токенам (берем последний скор для каждого)
        token_scores = {}
        for score in scores:
            token_id = str(score.token_id)
            if token_id not in token_scores:
                token_scores[token_id] = score
        
        # Сортируем по значению скора
        sorted_scores = sorted(
            token_scores.values(),
            key=lambda x: x.score_value,
            reverse=True
        )[:limit]
        
        # Формируем результат
        result = []
        for score in sorted_scores:
            result.append({
                "token_id": str(score.token_id),
                "score_value": score.score_value,
                "calculated_at": score.calculated_at,
                "components": score.components
            })
        
        return result


class CRUDBirdeyeRawData(CRUDBase[BirdeyeRawData, dict, dict]):
    """
    CRUD операции для raw данных Birdeye
    """

    def get_by_token_and_endpoint(
        self, 
        db: Session, 
        *, 
        token_address: str,
        endpoint: str,
        include_expired: bool = False
    ) -> List[BirdeyeRawData]:
        """
        Получить raw данные для токена и endpoint
        """
        query = db.query(BirdeyeRawData).filter(
            and_(
                BirdeyeRawData.token_address == token_address,
                BirdeyeRawData.endpoint == endpoint
            )
        )
        
        if not include_expired:
            query = query.filter(BirdeyeRawData.expires_at > datetime.now())
        
        return query.order_by(desc(BirdeyeRawData.fetched_at)).all()

    def get_latest_data(
        self, 
        db: Session, 
        *, 
        token_address: str,
        endpoint: str
    ) -> Optional[BirdeyeRawData]:
        """
        Получить последние данные для токена и endpoint
        """
        return (
            db.query(BirdeyeRawData)
            .filter(
                and_(
                    BirdeyeRawData.token_address == token_address,
                    BirdeyeRawData.endpoint == endpoint,
                    BirdeyeRawData.expires_at > datetime.now()
                )
            )
            .order_by(desc(BirdeyeRawData.fetched_at))
            .first()
        )

    def cleanup_expired_data(self, db: Session) -> int:
        """
        Очистка устаревших raw данных
        """
        deleted_count = (
            db.query(BirdeyeRawData)
            .filter(BirdeyeRawData.expires_at <= datetime.now())
            .delete()
        )
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired raw data records")
        return deleted_count

    def get_storage_stats(self, db: Session) -> Dict[str, Any]:
        """
        Статистика хранения raw данных
        """
        total_records = db.query(BirdeyeRawData).count()
        expired_records = db.query(BirdeyeRawData).filter(
            BirdeyeRawData.expires_at <= datetime.now()
        ).count()
        
        # Группировка по endpoint
        from sqlalchemy import func
        endpoint_stats = (
            db.query(
                BirdeyeRawData.endpoint,
                func.count(BirdeyeRawData.id).label('count')
            )
            .group_by(BirdeyeRawData.endpoint)
            .all()
        )
        
        endpoint_counts = {stat.endpoint: stat.count for stat in endpoint_stats}
        
        return {
            "total_records": total_records,
            "expired_records": expired_records,
            "active_records": total_records - expired_records,
            "by_endpoint": endpoint_counts
        }


# Создаем экземпляры CRUD для использования
token_metrics_crud = CRUDTokenMetrics(TokenMetrics)
token_scores_crud = CRUDTokenScores(TokenScores)
birdeye_raw_data_crud = CRUDBirdeyeRawData(BirdeyeRawData)
