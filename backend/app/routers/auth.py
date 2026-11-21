from fastapi import APIRouter, Depends
from app.models.api_models import (
    SignUpRequestBody,
    SignUpResponseBody,
    VerifyOtpRequestBody,
    VerifyOtpResponseBody,
    ResendOtpRequestBody,
    ResendOtpResponseBody,
    LoginRequestBody,
    LoginResponseBody,
    AnonymousResponseBody,
    MeResponseBody,
    LogoutResponseBody,
    AuthUser
)
from app.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=SignUpResponseBody)
def signup(body: SignUpRequestBody) -> SignUpResponseBody:
    result = AuthService.signup(
        email=body.email,
        phone=body.phone,
        password=body.password,
        name=body.name,
        otp_channel=body.otp_channel or "email"
    )
    return SignUpResponseBody(**result)

@router.post("/verify-otp", response_model=VerifyOtpResponseBody)
def verify_otp(body: VerifyOtpRequestBody) -> VerifyOtpResponseBody:
    result = AuthService.verify_otp(
        email=body.email,
        phone=body.phone,
        code=body.code,
        flow=body.flow or "signup"
    )
    return VerifyOtpResponseBody(**result)

@router.post("/resend-otp", response_model=ResendOtpResponseBody)
def resend_otp(body: ResendOtpRequestBody) -> ResendOtpResponseBody:
    result = AuthService.resend_otp(
        email=body.email,
        phone=body.phone,
        flow=body.flow or "signup",
        otp_channel=body.otp_channel or "email"
    )
    return ResendOtpResponseBody(**result)

@router.post("/login", response_model=LoginResponseBody)
def login(body: LoginRequestBody) -> LoginResponseBody:
    result = AuthService.login(
        email=body.email,
        phone=body.phone,
        password=body.password
    )
    return LoginResponseBody(**result)

@router.post("/anonymous", response_model=AnonymousResponseBody)
def anonymous() -> AnonymousResponseBody:
    result = AuthService.create_anonymous()
    return AnonymousResponseBody(**result)

@router.get("/me", response_model=MeResponseBody)
def me(current_user: AuthUser = Depends(get_current_user)) -> MeResponseBody:
    return MeResponseBody(user=current_user)

@router.post("/logout", response_model=LogoutResponseBody)
def logout() -> LogoutResponseBody:
    return LogoutResponseBody(success=True, message="Successfully logged out")

