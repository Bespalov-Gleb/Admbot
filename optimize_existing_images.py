#!/usr/bin/env python3
"""
Скрипт для оптимизации существующих изображений
Уменьшает размер JPEG с quality=95 до quality=85
Это уменьшит размер файлов на 20-30% без видимой потери качества
"""

import os
from PIL import Image
import sys

def optimize_image(file_path):
    """Оптимизирует одно изображение"""
    try:
        img = Image.open(file_path)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Получаем размер до оптимизации
        original_size = os.path.getsize(file_path)
        
        # Сохраняем с новым качеством
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            img.save(file_path, 'JPEG', quality=85, optimize=True, progressive=True)
        else:
            img.save(file_path, 'PNG', optimize=True)
        
        # Получаем размер после оптимизации
        new_size = os.path.getsize(file_path)
        saved = original_size - new_size
        saved_percent = (saved / original_size) * 100 if original_size > 0 else 0
        
        return True, saved, saved_percent
    
    except Exception as e:
        return False, 0, 0

def main():
    base_dirs = ['uploads', 'promotions']
    
    total_saved = 0
    total_files = 0
    failed_files = 0
    
    print("🔍 Начинаем оптимизацию изображений...")
    print()
    
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            continue
        
        print(f"📁 Обрабатываем директорию: {base_dir}/")
        
        # Проходим по всем поддиректориям
        for subdir in os.listdir(base_dir):
            subdir_path = os.path.join(base_dir, subdir)
            if not os.path.isdir(subdir_path):
                continue
            
            print(f"  └─ {subdir}/")
            
            # Обрабатываем все изображения в поддиректории
            for filename in os.listdir(subdir_path):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                file_path = os.path.join(subdir_path, filename)
                success, saved, saved_percent = optimize_image(file_path)
                
                total_files += 1
                
                if success:
                    total_saved += saved
                    print(f"     ✓ {filename}: {saved/1024:.1f} KB ({saved_percent:.1f}%)")
                else:
                    failed_files += 1
                    print(f"     ✗ {filename}: ошибка")
    
    print()
    print("=" * 60)
    print(f"✅ Оптимизация завершена!")
    print(f"📊 Обработано файлов: {total_files}")
    print(f"💾 Сэкономлено места: {total_saved/1024/1024:.2f} MB")
    print(f"❌ Ошибок: {failed_files}")
    print("=" * 60)
    
    if failed_files > 0:
        print()
        print("⚠️  Некоторые файлы не удалось оптимизировать.")
        print("    Проверьте права доступа и формат файлов.")
    
    return 0 if failed_files == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

