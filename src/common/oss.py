import argparse
import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2.models import PutObjectRequest

def main():
    # 从环境变量中加载凭证信息，用于身份验证
    credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
    # 加载SDK的默认配置，并设置凭证提供者
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider

    # 方式一：只填写Region（推荐）
    # 必须指定Region ID，以华东1（杭州）为例，Region填写为cn-hangzhou，SDK会根据Region自动构造HTTPS访问域名
    cfg.region = 'cn-hangzhou' 

    # 使用配置好的信息创建OSS客户端
    client = oss.Client(cfg)

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Upload file to OSS')
    parser.add_argument('file_path', help='Path to the file to upload')
    args = parser.parse_args()

    # 获取文件名作为object_name
    import os
    object_name = os.path.basename(args.file_path)

    # 3. 执行上传
    with open(args.file_path, 'rb') as file_obj:
        request = PutObjectRequest(
            bucket="shenyuan-x",
            key=object_name,
            body=file_obj
        )
        try:
            response = client.put_object(request)
            print(f"上传成功！ETag: {response.etag}, VersionId: {response.version_id}")
        except Exception as e:
            print(f"上传失败: {str(e)}")

    

if __name__ == "__main__":
    main()