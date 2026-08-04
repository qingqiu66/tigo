import random

def generate_random_dui() -> str:
    # 1. 随机生成前 8 位数字
    digits_list = [random.randint(0, 9) for _ in range(8)]
    
    # 2. 计算加权和与校验码
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total_sum = sum(d * w for d, w in zip(digits_list, weights))
    
    remainder = total_sum % 10
    check_digit = 0 if remainder == 0 else 10 - remainder
    
    # 3. 格式化输出
    digits_str = "".join(map(str, digits_list))
    return f"{digits_str}-{check_digit}"

# 示例：生成 5 个有效 DUI
for _ in range(5):
    print(generate_random_dui())