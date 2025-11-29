from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, with_loader_criteria

from app.infrastructure.database.models.base import Base


@event.listens_for(Session, "do_orm_execute")
def _filter_by_is_active(execute_state):
    
    if not execute_state.is_select:
        return
    
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        
        if hasattr(model_class, 'is_active'):
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    model_class,
                    lambda cls: cls.is_active == True,
                    include_aliases=True
                )
            )


