"""AI Image Upscaling for Apple Silicon - Sequential Lanczos + PyTorch Bicubic.

Este modulo provee upscaling de maxima calidad usando:
1. LANCZOS 4x (resize inicial)
2. PyTorch Bicubic refinement (GPU)
3. Contrast + Brightness + Sharpening
"""
import os
import sys
import torch
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def check_ai_support():
    """Check available AI/GPU support."""
    has_mps = torch.backends.mps.is_available()
    has_cuda = torch.cuda.is_available()

    return {
        'mps': has_mps,
        'cuda': has_cuda,
        'cpu': True,
        'device_name': "Apple Silicon" if has_mps else ('NVIDIA GPU' if has_cuda else 'CPU'),
        'available': has_mps or has_cuda or True,
        'realesrgan_available': False,
        'message': 'Lanczos + Bicubic 4x (M4)' if has_mps else 'Lanczos + Bicubic 4x'
    }


def try_load_realesrgan():
    """Try to load Real-ESRGAN if available."""
    try:
        from realesrgan import RealESRGANer
        return True
    except ImportError:
        return False


class HighQualityUpscaler:
    """High quality upscaler using sequential Lanczos + PyTorch Bicubic + Enhancement."""

    def __init__(self, scale=2):
        self.scale = scale
        self.device = self._get_device()

    def _get_device(self):
        """Get the best available device."""
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    def upscale(self, input_path, output_path=None):
        """Upscale image using sequential Lanczos + PyTorch Bicubic.

        Flow:
        1. LANCZOS 4x (initial resize)
        2. PyTorch bicubic refinement (GPU)
        3. Contrast + Brightness + Sharpening
        """
        try:
            img = Image.open(input_path).convert('RGB')
            original_width, original_height = img.size

            target_width = original_width * self.scale
            target_height = original_height * self.scale

            # Step 1: Lanczos 4x initial resize
            img_lanczos = img.resize(
                (target_width, target_height),
                Image.Resampling.LANCZOS
            )

            # Step 2: PyTorch bicubic refinement (only on GPU)
            if self.device.type in ('mps', 'cuda'):
                img_np = np.array(img_lanczos)

                # Convert to tensor
                img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).float() / 255.0
                img_tensor = img_tensor.unsqueeze(0).to(self.device)

                # Bicubic refinement
                img_tensor = torch.nn.functional.interpolate(
                    img_tensor,
                    size=(target_height, target_width),
                    mode='bicubic',
                    align_corners=False,
                    antialias=True
                )

                img_tensor = img_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
                img_np = (img_tensor * 255).clip(0, 255).astype(np.uint8)

                result = Image.fromarray(img_np)
            else:
                result = img_lanczos

            # Step 3: Enhancement pipeline
            # Contrast enhancement
            result = ImageEnhance.Contrast(result).enhance(1.1)

            # Brightness adjustment
            result = ImageEnhance.Brightness(result).enhance(1.02)

            # Sharpening with UnsharpMask
            unsharp = ImageFilter.UnsharpMask(
                radius=2.0,
                percent=120,
                threshold=1
            )
            result = result.filter(unsharp)

            # Save with high quality
            if output_path is None:
                output_path = input_path

            result.save(output_path, quality=95, optimize=True)

            return output_path

        except Exception as e:
            print(f"Error en upscale: {e}")
            return None

    def cleanup(self):
        """Clean up GPU resources."""
        if self.device.type == 'mps':
            torch.mps.empty_cache()
        elif self.device.type == 'cuda':
            torch.cuda.empty_cache()


class RealESRGANUpscaler:
    """Real-ESRGAN upscaler (requires manual installation of basicsr)."""

    def __init__(self, scale=2, tile_size=400):
        self.scale = scale
        self.tile_size = tile_size
        self.device = self._get_device()
        self.upsampler = None
        self.model_path = None

    def _get_device(self):
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    def load_model(self):
        """Load Real-ESRGAN model."""
        if not try_load_realesrgan():
            return False

        try:
            from realesrgan import RealESRGANer

            model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            model_path = os.path.join(os.path.dirname(__file__), 'models', f'RealESRGAN_x{self.scale}plus.pth')
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            if not os.path.exists(model_path):
                print(f"Descargando modelo Real-ESRGAN x{self.scale}...")
                import urllib.request
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                urllib.request.urlretrieve(model_url, model_path)

            self.upsampler = RealESRGANer(
                scale=self.scale,
                model_path=model_path,
                device=self.device,
                tile=self.tile_size,
                tile_pad=10,
                pre_pad=0,
                half=False
            )
            return True

        except Exception as e:
            print(f"Error cargando Real-ESRGAN: {e}")
            return False

    def upscale(self, input_path, output_path=None):
        """Upscale using Real-ESRGAN."""
        if self.upsampler is None:
            if not self.load_model():
                return None

        try:
            img = Image.open(input_path).convert('RGB')
            img_np = np.array(img)

            output, _ = self.upsampler.enhance(img_np, outscale=self.scale)
            result = Image.fromarray(output)

            if output_path is None:
                output_path = input_path

            result.save(output_path, quality=95, optimize=True)
            return output_path

        except Exception as e:
            print(f"Error Real-ESRGAN: {e}")
            return None

    def cleanup(self):
        if self.device.type == 'mps':
            torch.mps.empty_cache()
        elif self.device.type == 'cuda':
            torch.cuda.empty_cache()


def upscale_image_ai(image_path, scale=2, use_mps=True, output_path=None):
    """Convenience function to upscale a single image."""
    if use_mps and torch.backends.mps.is_available():
        device = torch.device('mps')
    elif use_mps and torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    upscaler = HighQualityUpscaler(scale=scale)
    upscaler.device = device
    result = upscaler.upscale(image_path, output_path)
    upscaler.cleanup()
    return result


def get_estimated_time(pages_count, scale):
    """Estimate conversion time based on page count and scale."""
    # M4 is very fast, estimate based on M4 performance
    if torch.backends.mps.is_available():
        per_page = 2.5 if scale == 4 else 1.2
    elif torch.cuda.is_available():
        per_page = 3 if scale == 4 else 1.5
    else:
        per_page = 8 if scale == 4 else 4

    total_seconds = int(pages_count * per_page)
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"~{minutes}m {seconds}s"