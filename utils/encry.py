import os
import base64

from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

from utils.logs import ExceptionLog

class UnitEncry:
    '''
    通用加密类:
    1、密钥管理 - 生成密钥和读取已有密钥
    2、加密解密 - 加密解密内容判断
    '''
    def __init__(self) -> None:
        self._e: ExceptionLog = ExceptionLog.get_instance()
        self._init_encryp_key()
        self._generate_rsa_key_file()

    @property
    def aes_key(self) -> str:
        return self._key.decode("utf-8")

    @property
    def rsa_pub_key(self) -> str:
        return self._rsa_pub_key.decode("utf-8")

    def _generate_rsa_key_file(self) -> bool:
        private_key_file: Path = Path(__file__).parent.parent / "private_key.pem"
        public_key_file: Path = Path(__file__).parent.parent / "public_key.pem"

        try:
            if not os.path.exists(private_key_file): Path(private_key_file).touch()
            if not os.path.exists(public_key_file): Path(public_key_file).touch()
            if os.path.getsize(private_key_file) != 0 and os.path.getsize(public_key_file) != 0:
                with open(private_key_file, "rb") as f: self._rsa_pri_key: bytes = f.read()
                with open(public_key_file, "rb") as f: self._rsa_pub_key: bytes = f.read()
            else:
                self._generate_rsa_key_pair()
                with open(private_key_file, "wb") as f:
                    f.truncate(0)
                    f.write(self._rsa_pri_key)
                with open(public_key_file, "wb") as f:
                    f.truncate(0)
                    f.write(self._rsa_pub_key)
            return True
        except Exception as err:
            self._e.handle_exception(err)
            self._e.error("生成密钥文件失败")
            os.remove(private_key_file)
            os.remove(public_key_file)
            return False

    def _generate_rsa_key_pair(self) -> None:
        # 生成rsa私钥
        private_key: rsa.RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        # 根据私钥获取公钥
        public_key: rsa.RSAPublicKey = private_key.public_key()

        # 序列化私钥为 PEM 编码 + PKCS#8 格式 + 密码加密
        self._rsa_pri_key: bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8, # 推荐：PKCS#8 格式
            encryption_algorithm=serialization.BestAvailableEncryption(self._key)
        )

        # 序列化公钥为 PEM 编码 + 标准格式
        self._rsa_pub_key: bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _init_encryp_key(self) -> None:
        target_file: Path = Path(__file__).parent.parent / "secret.key"

        try:
            if not os.path.exists(target_file): Path(target_file).touch()
            if os.path.getsize(target_file) != 0:
                with open(target_file, "rb") as f:
                    self._key: bytes = f.read()
                    self._frenet: Fernet = Fernet(self._key)
            else:
                key: bytes = Fernet.generate_key() # 返回一个32位随机数经过base64编码后的bytes对象
                with open(target_file, "wb") as f: f.write(key)
                self._key: bytes = key
                self._frenet: Fernet = Fernet(self._key)
        except Exception as err:
            self._e.handle_exception(err)
            self._e.error("初始化密钥文件失败")
            os.remove(target_file)
            return

    def _verify_signature(self, data: list, signature: str) -> bool:
        public_key: rsa.RSAPublicKey = serialization.load_pem_public_key( # type: ignore
            self._rsa_pub_key,
            backend=default_backend()
        )
        try:
            public_key.verify(
                bytes.fromhex(signature),
                data=str(data).encode("utf-8"),
                padding=padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                algorithm=hashes.SHA256()
            )
            self._e.info("签名验证成功")
            return True
        except InvalidSignature as e:
            self._e.info("签名验证失败,无效的签名")
            return False
        except ValueError as e:
            self._e.handle_exception(e)
            self._e.info("签名验证失败,值错误")
            return False
        except Exception as e:
            self._e.handle_exception(e)
            self._e.info("签名验证失败,验证方法错误")
            return False

    def generate_signature_str(self, data: list) -> str:
        private_key: rsa.RSAPrivateKey = serialization.load_pem_private_key( # type: ignore
            self._rsa_pri_key,
            password=self._key,
            backend=default_backend()
        )
        signature: bytes = private_key.sign(
            data=str(data).encode("utf-8"),
            padding=padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )
        return signature.hex()

    def verify_signature(self, data: list, signature: str) -> bool:
        return self._verify_signature(data, signature)

    def generate_encry_str(self, val: str) -> str:
        # pub_str: str = json.dumps(str(val))
        encode_data: str = base64.urlsafe_b64encode(val.encode()).decode()
        encryt_data: str = self._frenet.encrypt(encode_data.encode()).decode()
        return encryt_data

    def parse_encry_str(self, val: str) -> str | None:
        try:
            decryp_data: str = self._frenet.decrypt(val.encode()).decode()
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("解密数据失败")
            return
        decode_data: str = base64.urlsafe_b64decode(decryp_data.encode()).decode()
        return decode_data
