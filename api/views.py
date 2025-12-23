import re
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MyUser


def index(request):
    return Response({"message": "Welcome to my API!"})

class SignUpView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        password = request.data.get("password")

        # 必須項目チェック
        if not user_id or not password:
            return Response(
                {
                    "message": "Account creation failed",
                    "cause": "Required user_id and password",
                },
                status=400,
            )

        # 値の長さチェック
        if not (6 <= len(user_id) <= 20) or not (8 <= len(password) <= 20):
            return Response(
                {
                    "message": "Account creation failed",
                    "cause": "Input length is incorrect",
                },
                status=400,
            )

        # 文字の種類チェック
        if not re.fullmatch(r"[A-Za-z0-9]+", user_id):
            return Response(
                {
                    "message": "Account creation failed",
                    "cause": "Incorrect character pattern",
                },
                status=400,
            )

        if not re.fullmatch(r"[\x21-\x7E]+", password):
            return Response(
                {
                    "message": "Account creation failed",
                    "cause": "Incorrect character pattern",
                },
                status=400,
            )

        # 重複チェック
        if MyUser.objects.filter(user_id=user_id).exists():
            return Response(
                {
                    "message": "Account creation failed",
                    "cause": "Already same user_id is used",
                },
                status=400,
            )

        # アカウント作成処理
        user = MyUser.objects.create(
            user_id=user_id, password=password, nickname=user_id
        )

        return Response(
            {
                "message": "Account successfully created",
                "user": {"user_id": user.user_id, "nickname": user.nickname},
            },
            status=200,
        )


class UserView(APIView):
    def get(self, request, user_id):
        auth_header = request.headers.get("Authorization")

        # 認証チェック
        if not auth_header or not auth_header.startswith("Basic "):
            return Response({"message": "Authentication failed"}, status=401)

        # Basic認証のデコード
        try:
            auth_encoded = auth_header.split(" ")[1]
            decoded = base64.b64decode(auth_encoded).decode("utf-8")
            auth_user_id, password = decoded.split(":", 1)
        except Exception:
            return Response({"message": "Authentication failed"}, status=401)

        # ユーザー存在確認
        try:
            user = MyUser.objects.get(user_id=user_id)
        except MyUser.DoesNotExist:
            return Response({"message": "No user found"}, status=404)

        # 認証情報と一致するか確認
        if user.user_id != auth_user_id or user.password != password:
            return Response({"message": "Authentication failed"}, status=401)

        # nicknameの補完処理
        nickname = user.nickname if user.nickname else user.user_id

        user_data = {"user_id": user.user_id, "nickname": nickname}

        if user.comment:
            user_data["comment"] = user.comment

        return Response(
            {"message": "User details by user_id", "user": user_data}, status=200
        )

    def patch(self, request, user_id):

        # Authorizationヘッダーの取得
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response({"message": "Authentication failed"}, status=401)

        # Basic認証のデコード
        try:
            auth_encoded = auth_header.split(" ")[1]
            decoded = base64.b64decode(auth_encoded).decode("utf-8")
            auth_user_id, password = decoded.split(":", 1)
        except Exception:
            return Response({"message": "Authentication failed"}, status=401)

        # 該当ユーザー取得
        try:
            user = MyUser.objects.get(user_id=user_id)
        except MyUser.DoesNotExist:
            return Response({"message": "No user found"}, status=404)

        # 認証一致チェック
        if user.user_id != auth_user_id:
            return Response({"message": "No permission for update"}, status=403)
        if user.password != password:
            return Response({"message": "Authentication failed"}, status=401)

        # user_id, password更新試みをブロック
        if "user_id" in request.data or "password" in request.data:
            return Response(
                {
                    "message": "User updation failed",
                    "cause": "Not updatable user_id and password",
                },
                status=400,
            )

        # nickname, commentの取得
        nickname = request.data.get("nickname")
        comment = request.data.get("comment")

        if nickname is None and comment is None:
            return Response(
                {
                    "message": "User updation failed",
                    "cause": "Required nickname or comment",
                },
                status=400,
            )

        # バリデーション関数
        def is_valid_string(s, max_len):
            return len(s) <= max_len and re.fullmatch(r"[^\x00-\x1F\x7F]*", s)

        # nickname 処理(バリデーションと補完)
        if nickname is not None:
            if nickname == "":
                user.nickname = user.user_id
            elif not is_valid_string(nickname, 30):
                return Response(
                    {
                        "message": "User updation failed",
                        "cause": "String length limit exceeded or containing invalid characters",
                    },
                    status=400,
                )
            else:
                user.nickname = nickname

        # comment 処理(バリデーションと補完)
        if comment is not None:
            if comment == "":
                user.comment = ""
            elif not is_valid_string(comment, 100):
                return Response(
                    {
                        "message": "User updation failed",
                        "cause": "String length limit exceeded or containing invalid characters",
                    },
                    status=400,
                )
            else:
                user.comment = comment

        # 保存
        user.save()

        # 成功時のレスポンスデータ構築かつ送出
        response_data = {"user_id": user.user_id}

        if user.comment:
            response_data["comment"] = user.comment

        if user.nickname:
            response_data["nickname"] = user.nickname

        return Response(
            {"message": "User successfully updated", "user": response_data}, status=200
        )


class CloseUserView(APIView):
    def post(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Basic "):
            return Response({"message": "Authentication failed"}, status=401)

        # Basic認証のデコード
        try:
            auth_encoded = auth_header.split(" ")[1]
            decoded = base64.b64decode(auth_encoded).decode("utf-8")
            user_id, password = decoded.split(":", 1)
        except Exception:
            return Response({"message": "Authentication failed"}, status=401)

        # ユーザーの認証
        try:
            user = MyUser.objects.get(user_id=user_id)
        except MyUser.DoesNotExist:
            return Response({"message": "Authentication failed"}, status=401)

        if user.password != password:
            return Response({"message": "Authentication failed"}, status=401)

        # 認証成功 → アカウント削除
        user.delete()

        return Response(
            {"message": "Account and user successfully removed"}, status=200
        )
