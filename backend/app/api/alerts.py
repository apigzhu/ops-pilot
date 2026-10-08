"""告警规则、告警事件与 AI 诊断接口。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import ai
from app.database import get_db
from app.models import Alert, AlertDiagnosis, AlertRule
from app.schemas import AlertOut, AlertRuleIn, AlertRuleOut, DiagnosisOut

router = APIRouter(prefix="/api/v1", tags=["alerts"])


@router.post("/alert-rules", response_model=AlertRuleOut, status_code=201)
def create_rule(payload: AlertRuleIn, db: Session = Depends(get_db)) -> AlertRule:
    """创建一条告警规则。"""
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/alert-rules", response_model=list[AlertRuleOut])
def list_rules(db: Session = Depends(get_db)) -> list[AlertRule]:
    """列出所有告警规则。"""
    return list(db.scalars(select(AlertRule).order_by(AlertRule.id)))


@router.delete("/alert-rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)) -> None:
    """删除一条告警规则。"""
    rule = db.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="rule not found")
    db.delete(rule)
    db.commit()


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status: str | None = Query(default=None, pattern="^(firing|resolved)$"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Alert]:
    """列出告警事件，可按状态过滤（firing / resolved）。"""
    stmt = select(Alert).order_by(Alert.triggered_at.desc()).limit(limit)
    if status:
        stmt = (
            select(Alert)
            .where(Alert.status == status)
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
        )
    return list(db.scalars(stmt))


@router.post("/alerts/{alert_id}/diagnose", response_model=DiagnosisOut)
def diagnose_alert(alert_id: int, db: Session = Depends(get_db)) -> AlertDiagnosis:
    """对一条告警执行 AI 故障诊断（已存在则重新生成）。"""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return ai.diagnose(db, alert)


@router.get("/alerts/{alert_id}/diagnosis", response_model=DiagnosisOut)
def get_diagnosis(alert_id: int, db: Session = Depends(get_db)) -> AlertDiagnosis:
    """获取某条告警已有的 AI 诊断结果。"""
    record = db.scalar(
        select(AlertDiagnosis).where(AlertDiagnosis.alert_id == alert_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="diagnosis not found")
    return record
