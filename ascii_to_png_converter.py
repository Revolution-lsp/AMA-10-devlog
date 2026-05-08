import base64
import os
import re
from typing import Optional, Tuple
from PIL import Image
import io

class DataURIToPNG:
    """Data URI图片解码并保存为PNG工具类"""
    
    # 支持的图片MIME类型
    SUPPORTED_MIME_TYPES = {
        'image/jpeg': 'JPEG',
        'image/jpg': 'JPEG',
        'image/png': 'PNG',
        'image/gif': 'GIF',
        'image/bmp': 'BMP',
        'image/webp': 'WEBP',
        'image/svg+xml': 'SVG',
        'image/tiff': 'TIFF',
    }
    
    def __init__(self):
        """初始化转换器"""
        self.data_uri_pattern = re.compile(
            r'^data:([^;]+);base64,(.+)$',
            re.IGNORECASE
        )
    
    def parse_data_uri(self, data_uri: str) -> Tuple[str, str]:
        """
        解析Data URI字符串
        
        Args:
            data_uri: Data URI格式的字符串
            
        Returns:
            (mime_type, base64_data) 元组
        """
        # 清理字符串
        data_uri = data_uri.strip()
        
        # 尝试匹配Data URI格式
        match = self.data_uri_pattern.match(data_uri)
        
        if match:
            mime_type = match.group(1).lower()
            base64_data = match.group(2)
        else:
            # 如果不是标准的Data URI格式，尝试其他解析方式
            # 可能是JSON格式: type:"image",url:"data:image/jpeg;base64,..."
            json_match = re.search(r'data:(image/[^;]+);base64,([^"\'}\s]+)', data_uri)
            if json_match:
                mime_type = json_match.group(1).lower()
                base64_data = json_match.group(2)
            else:
                # 尝试直接当作base64处理
                raise ValueError(f"无法解析Data URI格式: {data_uri[:100]}...")
        
        # 清理base64数据（移除可能的换行和空格）
        base64_data = re.sub(r'\s+', '', base64_data)
        
        return mime_type, base64_data
    
    def decode_base64(self, base64_data: str) -> bytes:
        """
        解码Base64数据
        
        Args:
            base64_data: Base64编码的字符串
            
        Returns:
            解码后的二进制数据
        """
        try:
            # 添加padding（如果需要）
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            
            # 解码
            return base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Base64解码失败: {e}")
    
    def image_bytes_to_pil(self, image_bytes: bytes) -> Image.Image:
        """
        将图片字节数据转换为PIL Image对象
        
        Args:
            image_bytes: 图片二进制数据
            
        Returns:
            PIL Image对象
        """
        try:
            # 使用BytesIO从内存中读取图片
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            return image
        except Exception as e:
            raise ValueError(f"图片加载失败: {e}")
    
    def convert_to_png(self, image: Image.Image) -> Image.Image:
        """
        将图片转换为PNG格式（如果需要）
        
        Args:
            image: PIL Image对象
            
        Returns:
            PNG格式的Image对象
        """
        # 如果图片有透明通道，保持RGBA
        if image.mode in ('RGBA', 'LA', 'P'):
            # 转换为RGBA以保持透明通道
            return image.convert('RGBA')
        else:
            # 转换为RGB
            return image.convert('RGB')
    
    def save_as_png(self, image: Image.Image, output_path: str, 
                    optimize: bool = True) -> str:
        """
        保存图片为PNG格式
        
        Args:
            image: PIL Image对象
            output_path: 输出文件路径
            optimize: 是否优化PNG文件大小
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保输出路径以.png结尾
            if not output_path.lower().endswith('.png'):
                output_path += '.png'
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 转换为PNG格式并保存
            png_image = self.convert_to_png(image)
            png_image.save(output_path, 'PNG', optimize=optimize)
            
            return output_path
        except Exception as e:
            raise IOError(f"PNG文件保存失败: {e}")
    
    def process_data_uri(self, data_uri: str, output_path: str,
                        show_info: bool = True) -> Tuple[str, dict]:
        """
        处理Data URI并保存为PNG（完整流程）
        
        Args:
            data_uri: Data URI字符串
            output_path: PNG输出文件路径
            show_info: 是否显示处理信息
            
        Returns:
            (output_path, info_dict) 元组
        """
        try:
            # 解析Data URI
            mime_type, base64_data = self.parse_data_uri(data_uri)
            
            if show_info:
                print(f"检测到图片类型: {mime_type}")
            
            # 解码Base64
            image_bytes = self.decode_base64(base64_data)
            
            if show_info:
                print(f"Base64数据大小: {len(base64_data)} 字符")
                print(f"解码后数据大小: {len(image_bytes)} 字节")
            
            # 转换为PIL图片
            image = self.image_bytes_to_pil(image_bytes)
            
            if show_info:
                print(f"图片尺寸: {image.size}")
                print(f"图片模式: {image.mode}")
            
            # 保存为PNG
            saved_path = self.save_as_png(image, output_path)
            
            # 获取文件信息
            file_size = os.path.getsize(saved_path)
            
            if show_info:
                print(f"PNG文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")
            
            info = {
                'original_mime': mime_type,
                'image_size': image.size,
                'image_mode': image.mode,
                'file_size': file_size,
                'output_path': saved_path
            }
            
            return saved_path, info
            
        except Exception as e:
            raise Exception(f"转换失败: {e}")
    
    def process_json_entry(self, json_string: str, output_path: str,
                          show_info: bool = True) -> Tuple[str, dict]:
        """
        处理JSON格式的图片条目（如您提供的示例）
        
        Args:
            json_string: 包含图片信息的JSON字符串
            output_path: 输出文件路径
            show_info: 是否显示信息
            
        Returns:
            (output_path, info_dict) 元组
        """
        # 提取Data URI
        # 匹配模式: type:"image",url:"data:image/jpeg;base64,..."
        data_uri_match = re.search(r'url:"data:([^"]+)"', json_string)
        if data_uri_match:
            data_uri = f"data:{data_uri_match.group(1)}"
            return self.process_data_uri(data_uri, output_path, show_info)
        else:
            raise ValueError("无法从JSON中提取Data URI")

def main():
    """主函数 - 命令行交互式使用"""
    converter = DataURIToPNG()
    
    print("Data URI图片解码转PNG工具")
    print("-" * 50)
    print("支持的输入格式:")
    print("1. 标准格式: data:image/jpeg;base64,...")
    print("2. JSON格式: type:\"image\",url:\"data:image/jpeg;base64,...\"")
    print("3. 纯Base64数据")
    
    while True:
        print("\n请选择操作:")
        print("1. 粘贴Data URI进行转换")
        print("2. 从文件读取Data URI")
        print("3. 使用示例数据演示")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            # 手动输入Data URI
            print("\n请输入Data URI字符串（直接粘贴，按回车结束）:")
            print("（对于长字符串，请确保完整粘贴）")
            data_uri = input().strip()
            
            if not data_uri:
                print("错误: 输入为空")
                continue
            
            output_path = input("请输入输出PNG文件路径 (默认: output.png): ").strip()
            if not output_path:
                output_path = "output.png"
            
            try:
                saved_path, info = converter.process_data_uri(data_uri, output_path)
                
                print(f"\n✓ 转换成功!")
                print(f"  文件已保存到: {saved_path}")
                print(f"  图片尺寸: {info['image_size']}")
                print(f"  文件大小: {info['file_size']/1024:.1f} KB")
                
                # 询问是否打开
                open_img = input("\n是否打开图片查看? (y/n): ").strip().lower()
                if open_img == 'y':
                    try:
                        Image.open(saved_path).show()
                    except:
                        print("无法打开图片，请手动查看")
                
            except Exception as e:
                print(f"✗ 转换失败: {e}")
        
        elif choice == '2':
            # 从文件读取
            file_path = input("\n请输入包含Data URI的文件路径: ").strip()
            
            if not os.path.exists(file_path):
                print(f"错误: 文件 {file_path} 不存在")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                output_path = input("请输入输出PNG文件路径 (默认: output.png): ").strip()
                if not output_path:
                    output_path = "output.png"
                
                # 尝试JSON格式解析
                if 'type":' in content or 'url":' in content:
                    saved_path, info = converter.process_json_entry(content, output_path)
                else:
                    saved_path, info = converter.process_data_uri(content, output_path)
                
                print(f"\n✓ 转换成功!")
                print(f"  文件已保存到: {saved_path}")
                print(f"  图片尺寸: {info['image_size']}")
                
            except Exception as e:
                print(f"✗ 转换失败: {e}")
        
        elif choice == '3':
            # 演示模式
            demonstrate_with_sample()
        
        elif choice == '4':
            print("感谢使用，再见!")
            break
        
        else:
            print("无效选项，请重新选择")

def demonstrate_with_sample():
    """使用您提供的示例数据进行演示"""
    print("\n使用您提供的JPEG图片Data URI进行演示...")
    
    # 您提供的示例数据（简短版本，原始数据太长）
    # 这里使用一个简单的测试图片Data URI
    sample_data_uri = "data:image/jpeg;base64,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"
    
    converter = DataURIToPNG()
    
    try:
        saved_path, info = converter.process_data_uri(
            sample_data_uri, 
            "demo_output.png",
            show_info=True
        )
        
        print(f"\n✓ 演示转换成功!")
        print(f"  文件已保存到: {saved_path}")
        print(f"  图片尺寸: {info['image_size']}")
        print(f"  文件大小: {info['file_size']/1024:.1f} KB")
        
        # 尝试打开图片
        try:
            from PIL import Image
            Image.open(saved_path).show()
            print("  已打开图片预览")
        except:
            print("  无法自动打开图片，请手动查看")
            
    except Exception as e:
        print(f"✗ 演示失败: {e}")

def process_your_specific_format():
    """专门处理您提供的JSON格式"""
    # 您提供的完整示例数据
    your_data = 'type:"image",url:"data:image/jpeg;base64,/9j/4AAQSkZJRg..."'
    
    converter = DataURIToPNG()
    
    try:
        saved_path, info = converter.process_json_entry(
            your_data,
            "your_image.png",
            show_info=True
        )
        return saved_path, info
    except Exception as e:
        print(f"处理失败: {e}")
        return None, None

def batch_process():
    """批量处理多个Data URI文件"""
    converter = DataURIToPNG()
    
    # 假设你有一个包含多个JSON条目的文件
    sample_entries = [
        'type:"image",url:"data:image/jpeg;base64,..."',
        'type:"image",url:"data:image/png;base64,..."'
    ]
    
    results = []
    
    for i, entry in enumerate(sample_entries):
        try:
            output_path = f"image_{i+1}.png"
            saved_path, info = converter.process_json_entry(entry, output_path)
            results.append({
                'input': f"Entry {i+1}",
                'output': saved_path,
                'info': info
            })
            print(f"✓ 第{i+1}个图片转换成功: {saved_path}")
        except Exception as e:
            print(f"✗ 第{i+1}个图片转换失败: {e}")
    
    return results

if __name__ == "__main__":
    # 检查依赖
    try:
        from PIL import Image
    except ImportError:
        print("错误: 需要安装Pillow库")
        print("请运行: pip install Pillow")
        exit(1)
    
    print("Data URI图片解码转PNG工具")
    print("=" * 50)
    
    print("\n选择运行模式:")
    print("1. 交互模式")
    print("2. 快速演示（使用示例数据）")
    print("3. 退出")
    
    mode = input("\n请输入选项 (1/2/3): ").strip()
    
    if mode == '1':
        main()
    elif mode == '2':
        demonstrate_with_sample()
    elif mode == '3':
        print("退出程序")
    else:
        print("无效选择，运行演示模式")
        demonstrate_with_sample()
