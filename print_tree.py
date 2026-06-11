import os

def generate_clean_tree(startpath):
    # Các thư mục "béo phì" hoặc rác cần bỏ qua
    exclude_dirs = {'.git', '__pycache__', 'venv', 'raw', 'vector_db', 'node_modules', 'target', '.pytest_cache', '.idea'}
    
    print(f"📦 PROJECT ROOT: {os.path.abspath(startpath)}")
    for root, dirs, files in os.walk(startpath):
        # Lọc bỏ thư mục rác ngay từ vòng gửi xe
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * (level)
        folder_name = os.path.basename(root)
        
        if folder_name != '.':
            print(f'{indent}├── 📂 {folder_name}/')
            
        subindent = '│   ' * (level + 1)
        for f in files:
            # Bỏ qua các file ẩn không quan trọng
            if not f.startswith('.DS_Store'):
                print(f'{subindent}├── 📄 {f}')

if __name__ == "__main__":
    generate_clean_tree(".")