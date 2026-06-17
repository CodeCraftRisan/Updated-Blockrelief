import os
import base64

# যে ফাইল ফরম্যাটগুলো আমরা রিড করতে চাই
SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.sol': 'solidity',
    '.html': 'html',
    '.css': 'css',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.json': 'json',
    '.csv': 'text',
    '.txt': 'text',
    '.md': 'markdown'
}

# যে ফোল্ডার বা ফাইলগুলো আমরা ইগনোর করতে চাই
IGNORE_LIST = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv', 
    'env', '.ipynb_checkpoints', 'project_summary.md', 'code_to_md.py'
}

def generate_folder_tree(dir_path, prefix=""):
    """ফোল্ডার স্ট্রাকচার ভিজ্যুয়াল ট্রি তৈরি করার ফাংশন"""
    tree_str = ""
    try:
        items = sorted(os.listdir(dir_path))
    except PermissionError:
        return ""
    
    items = [item for item in items if item not in IGNORE_LIST]
    
    for i, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        
        tree_str += f"{prefix}{connector}{item}\n"
        
        if os.path.isdir(path):
            indent = "    " if is_last else "│   "
            tree_str += generate_folder_tree(path, prefix + indent)
            
    return tree_str

def main():
    root_dir = os.getcwd()
    output_file = os.path.join(root_dir, "project_summary.md")
    
    print("⏳ প্রজেক্ট অ্যানালাইসিস করা হচ্ছে (PNG ইমেজসহ)...")
    
    with open(output_file, "w", encoding="utf-8") as md:
        # ১. হেডলাইন ও প্রজেক্ট স্ট্রাকচার লেখা
        md.write("# Project Documentation & Source Code\n\n")
        md.write("## 📁 Project Directory Structure\n")
        md.write("```text\n")
        md.write(f"{os.path.basename(root_dir)}/\n")
        md.write(generate_folder_tree(root_dir))
        md.write("```\n\n")
        md.write("---\n\n")
        
        md.write("## 📄 File Contents & Media\n\n")
        
        # ২. পুরো ডিরেক্টরি স্ক্যান করে ফাইল রিড করা
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_LIST]
            
            for file in sorted(files):
                if file in IGNORE_LIST:
                    continue
                    
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                
                relative_path = os.path.relpath(file_path, root_dir)
                
                # ক) যদি সাধারণ কোড বা টেক্সট ফাইল হয়
                if ext_lower in SUPPORTED_EXTENSIONS:
                    lang = SUPPORTED_EXTENSIONS[ext_lower]
                    md.write(f"### 📂 File: `{relative_path}`\n\n")
                    md.write(f"```{lang}\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            md.write(content)
                    except Exception as e:
                        md.write(f"[Error reading file: {str(e)}]")
                    md.write("\n```\n\n")
                    md.write("---\n\n")
                
                # খ) যদি PNG ইমেজ ফাইল হয়
                elif ext_lower == '.png':
                    md.write(f"### 🖼️ Image File: `{relative_path}`\n\n")
                    try:
                        with open(file_path, "rb") as img_file:
                            # ইমেজটিকে Base64 এ কনভার্ট করা হচ্ছে যাতে মার্কডাউন ফাইলের ভেতরেই সরাসরি ইমেজ দেখা যায়
                            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                            md.write(f"![{file}](data:image/png;base64,{encoded_string})\n\n")
                    except Exception as e:
                        md.write(f"[Error reading image file: {str(e)}]\n\n")
                    md.write("---\n\n")
                    
    print(f"✅ সফলভাবে তৈরি হয়েছে! তোমার সব কোড ও ইমেজ এখন এখানে আছে: {output_file}")

if __name__ == "__main__":
    main()