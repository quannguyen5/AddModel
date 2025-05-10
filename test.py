import os
import json
import time
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

def check_kaggle_api():
    """Kiểm tra xem Kaggle API có hoạt động không"""
    print("Checking Kaggle API...")
    print(f"Python version: {sys.version}")
    
    # Khởi tạo API
    api = KaggleApi()
    try:
        api.authenticate()
        print("✅ Authentication successful")
        
        # Kiểm tra phiên bản API
        print(f"Kaggle API version: {api.__version__ if hasattr(api, '__version__') else 'Unknown'}")
        
        # Kiểm tra các phương thức có sẵn
        print("\nAvailable methods:")
        methods = [method for method in dir(api) if not method.startswith('_') and callable(getattr(api, method))]
        print(", ".join(methods[:20]) + "..." if len(methods) > 20 else "")
        
        # Kiểm tra quyền và hạn ngạch
        print("\nChecking permissions...")
        try:
            # List datasets
            print("Listing datasets...")
            datasets = api.dataset_list(mine=True)
            print(f"Found {len(datasets)} personal datasets")
            if datasets:
                print(f"Latest dataset: {datasets[0].ref}")
            
            # List kernels
            print("Listing kernels...")
            kernels = api.kernels_list(mine=True)
            print(f"Found {len(kernels)} personal kernels")
            if kernels:
                print(f"Latest kernel: {kernels[0].ref}")
            
            # Lấy username từ dataset hoặc kernel
            username = None
            if kernels:
                username = kernels[0].ref.split('/')[0]
            elif datasets:
                username = datasets[0].ref.split('/')[0]
            else:
                # Thử lấy từ kaggle.json
                try:
                    with open(os.path.expanduser('~/.kaggle/kaggle.json'), 'r') as f:
                        creds = json.load(f)
                        username = creds.get('username')
                except:
                    pass
            
            if not username:
                print("❌ Could not determine username. Please check your Kaggle credentials.")
                return
                
            print(f"Using username: {username}")
            
            # Thử tạo một dataset đơn giản
            print("\nTesting dataset creation...")
            temp_dir = "test_kaggle_dataset"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Tạo file test
            with open(os.path.join(temp_dir, "test.txt"), "w") as f:
                f.write("Test file")
            
            # Tạo metadata
            dataset_name = f"test-dataset-{int(time.time())}"
            with open(os.path.join(temp_dir, "dataset-metadata.json"), "w") as f:
                json.dump({
                    "title": "Test Dataset",
                    "id": f"{username}/{dataset_name}",
                    "licenses": [{"name": "CC0-1.0"}]
                }, f)
            
            # In ra thông tin metadata để debug
            print(f"Dataset metadata: {username}/{dataset_name}")
            
            # Thử tạo dataset
            try:
                api.dataset_create_new(temp_dir, convert_to_csv=False)
                print("✅ Dataset creation successful")
                
                # Thử tạo kernel
                print("\nTesting kernel creation...")
                kernel_dir = "test_kaggle_kernel"
                os.makedirs(kernel_dir, exist_ok=True)
                
                # Tạo metadata
                kernel_name = f"test-kernel-{int(time.time())}"
                with open(os.path.join(kernel_dir, "kernel-metadata.json"), "w") as f:
                    json.dump({
                        "id": f"{username}/{kernel_name}",
                        "title": f"Test Kernel {int(time.time())}",
                        "code_file": "script.py",
                        "language": "python",
                        "kernel_type": "script",
                        "is_private": True,
                        "enable_gpu": False,
                        "enable_internet": True,
                        "dataset_sources": [f"{username}/{dataset_name}"],
                        "competition_sources": [],
                        "kernel_sources": []
                    }, f)
                
                # Tạo script đơn giản
                with open(os.path.join(kernel_dir, "script.py"), "w") as f:
                    f.write('print("Hello from Kaggle Kernel")')
                
                # In ra nội dung thư mục kernel
                print(f"Kernel directory contents: {os.listdir(kernel_dir)}")
                
                # Thử push kernel
                print(f"Pushing kernel: {username}/{kernel_name}")
                cwd = os.getcwd()
                os.chdir(kernel_dir)  # Chuyển đến thư mục kernel
                try:
                    api.kernels_push(".")  # Sử dụng thư mục hiện tại
                    print("✅ Kernel creation successful")
                except Exception as ke:
                    print(f"❌ Failed to create kernel: {ke}")
                os.chdir(cwd)  # Trở lại thư mục ban đầu
                    
            except Exception as de:
                print(f"❌ Failed to create dataset: {de}")
                import traceback
                print(traceback.format_exc())
            
            # Dọn dẹp
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(kernel_dir):
                shutil.rmtree(kernel_dir)
                
        except Exception as e:
            print(f"❌ Permission check failed: {e}")
            import traceback
            print(traceback.format_exc())
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        import traceback
        print(traceback.format_exc())
        
    print("\nKaggle API check completed")

if __name__ == "__main__":
    check_kaggle_api()