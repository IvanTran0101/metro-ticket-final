import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, HTTPException, status

from notification_service.app.settings import settings
from notification_service.app.schemas import SendReceiptRequest

router = APIRouter()

@router.post("/internal/post/notification/send_receipt", status_code=status.HTTP_202_ACCEPTED)
def send_receipt(req: SendReceiptRequest):
    try:
        _send_email_receipt(req)
        return {"ok": True, "message": "Email queued"}
    except Exception as e:
        print(f"Email error: {e}")
        return {"ok": False, "message": str(e)}

def _send_email_receipt(req: SendReceiptRequest):
    if settings.DRY_RUN:
        print(f"[DRY RUN] Sending email to {req.email}: {req.amount}đ")
        return

    subject = f"Biên lai chuyến đi MetroFlow - {req.journey_code}"
    
    html = f"""
    <html>
        <body>
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd;">
                <h2 style="color: #28a745;">Thanh toán thành công</h2>
                <p>Xin chào,</p>
                <p>Cảm ơn bạn đã sử dụng dịch vụ MetroFlow. Dưới đây là chi tiết chuyến đi của bạn:</p>
                
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td><strong>Mã vé:</strong></td>
                        <td>{req.journey_code}</td>
                    </tr>
                    <tr>
                        <td><strong>Ngày đi:</strong></td>
                        <td>{req.date}</td>
                    </tr>
                    <tr>
                        <td><strong>Tổng tiền:</strong></td>
                        <td style="font-size: 18px; color: #d9534f;"><strong>{req.amount:,.0f} VND</strong></td>
                    </tr>
                </table>
                
                <p>Số dư ví hiện tại đã được cập nhật.</p>
                <p><i>Chúc bạn một ngày tốt lành!</i></p>
            </div>
        </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = req.email
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, req.email, msg.as_string())