from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, with_loader_criteria

from app.infrastructure.database.models.base import Base
from app.infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


def setup_active_filter():
    """
    Настройка автоматической фильтрации по полю is_active
    
    Для всех моделей с полем is_active автоматически добавляет
    фильтр WHERE is_active = True к SELECT запросам
    """
    
    @event.listens_for(Session, "do_orm_execute")
    def _filter_by_is_active(execute_state):
        """Автоматически фильтрует записи по is_active=True"""
        
        # Применяем только к SELECT запросам
        if not execute_state.is_select:
            return
        
        # Получаем все модели, которые наследуются от Base
        for mapper in Base.registry.mappers:
            model_class = mapper.class_
            
            # Проверяем есть ли у модели поле is_active
            if hasattr(model_class, 'is_active'):
                # Добавляем фильтр is_active=True для этой модели
                execute_state.statement = execute_state.statement.options(
                    with_loader_criteria(
                        model_class,
                        lambda cls: cls.is_active == True,
                        include_aliases=True
                    )
                )
    
    logger.info("active_filter_configured", message="Автоматическая фильтрация по is_active настроена")

