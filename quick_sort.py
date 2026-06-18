"""
快速排序算法实现
包含基础版本、原地排序版本和优化版本
"""

from typing import List, Callable, Any
import random


def quick_sort_basic(arr: List) -> List:
    """
    快速排序 - 基础版本（创建新列表）
    
    Args:
        arr: 待排序的列表
        
    Returns:
        排序后的新列表
    """
    if len(arr) <= 1:
        return arr
    
    # 选择中间元素作为基准
    pivot = arr[len(arr) // 2]
    
    # 分区
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    # 递归排序并合并
    return quick_sort_basic(left) + middle + quick_sort_basic(right)


def quick_sort_inplace(arr: List, low: int = 0, high: int = None) -> None:
    """
    快速排序 - 原地排序版本（空间复杂度更优）
    
    Args:
        arr: 待排序的列表（会被修改）
        low: 起始索引
        high: 结束索引
    """
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        # 获取分区点
        pivot_index = _partition(arr, low, high)
        
        # 递归排序左右子数组
        quick_sort_inplace(arr, low, pivot_index - 1)
        quick_sort_inplace(arr, pivot_index + 1, high)


def _partition(arr: List, low: int, high: int) -> int:
    """
    分区函数 - 使用最后一个元素作为基准
    
    Args:
        arr: 待分区的列表
        low: 起始索引
        high: 结束索引
        
    Returns:
        基准元素的最终位置索引
    """
    pivot = arr[high]  # 选择最后一个元素作为基准
    i = low - 1  # 较小元素的索引
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]  # 交换
    
    # 将基准元素放到正确位置
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def quick_sort_optimized(arr: List, low: int = 0, high: int = None) -> None:
    """
    快速排序 - 优化版本
    优化点：
    1. 三数取中法选择基准
    2. 小数组使用插入排序
    3. 尾递归优化（处理较大的子数组）
    
    Args:
        arr: 待排序的列表（会被修改）
        low: 起始索引
        high: 结束索引
    """
    if high is None:
        high = len(arr) - 1
    
    while low < high:
        # 小数组使用插入排序
        if high - low < 10:
            _insertion_sort(arr, low, high)
            break
        
        # 三数取中法选择基准
        pivot_index = _median_of_three(arr, low, high)
        arr[pivot_index], arr[high] = arr[high], arr[pivot_index]
        
        # 分区
        pivot_index = _partition(arr, low, high)
        
        # 尾递归优化：先处理较小的子数组
        if pivot_index - low < high - pivot_index:
            quick_sort_optimized(arr, low, pivot_index - 1)
            low = pivot_index + 1  # 尾递归优化
        else:
            quick_sort_optimized(arr, pivot_index + 1, high)
            high = pivot_index - 1  # 尾递归优化


def _median_of_three(arr: List, low: int, high: int) -> int:
    """
    三数取中法：选择 low、mid、high 三个位置的中位数作为基准
    
    Args:
        arr: 列表
        low: 起始索引
        high: 结束索引
        
    Returns:
        中位数元素的索引
    """
    mid = (low + high) // 2
    
    # 排序三个元素
    if arr[low] > arr[mid]:
        arr[low], arr[mid] = arr[mid], arr[low]
    if arr[low] > arr[high]:
        arr[low], arr[high] = arr[high], arr[low]
    if arr[mid] > arr[high]:
        arr[mid], arr[high] = arr[high], arr[mid]
    
    return mid


def _insertion_sort(arr: List, low: int, high: int) -> None:
    """
    插入排序（用于小数组优化）
    
    Args:
        arr: 列表
        low: 起始索引
        high: 结束索引
    """
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1
        while j >= low and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


def quick_sort_three_way(arr: List, low: int = 0, high: int = None) -> None:
    """
    快速排序 - 三路分区版本
    特别适合处理有大量重复元素的情况
    
    将数组分为三部分：< pivot, == pivot, > pivot
    
    Args:
        arr: 待排序的列表（会被修改）
        low: 起始索引
        high: 结束索引
    """
    if high is None:
        high = len(arr) - 1
    
    if low >= high:
        return
    
    # 随机选择pivot以避免最坏情况
    pivot_idx = random.randint(low, high)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    pivot = arr[high]
    
    lt = low      # arr[low..lt-1] < pivot
    i = low       # arr[lt..i-1] == pivot
    gt = high     # arr[gt+1..high] > pivot
    
    while i <= gt:
        if arr[i] < pivot:
            arr[lt], arr[i] = arr[i], arr[lt]
            lt += 1
            i += 1
        elif arr[i] > pivot:
            arr[i], arr[gt] = arr[gt], arr[i]
            gt -= 1
        else:
            i += 1
    
    # 递归排序小于和大于pivot的部分
    quick_sort_three_way(arr, low, lt - 1)
    quick_sort_three_way(arr, gt + 1, high)


def quick_sort(arr: List, key: Callable = None, reverse: bool = False) -> List:
    """
    快速排序的统一接口 - 推荐使用
    
    Args:
        arr: 待排序列表
        key: 排序键函数（可选），类似于Python内置sorted的key参数
        reverse: 是否降序排列
        
    Returns:
        排序后的新列表
        
    Examples:
        >>> quick_sort([3, 1, 4, 1, 5])
        [1, 1, 3, 4, 5]
        
        >>> quick_sort([3, 1, 4, 1, 5], reverse=True)
        [5, 4, 3, 1, 1]
        
        >>> quick_sort(["banana", "Apple", "cherry"], key=str.lower)
        ['Apple', 'banana', 'cherry']
    """
    if not arr:
        return []
    
    # 如果提供了key函数，转换为元组进行排序
    if key is not None:
        decorated = [(key(x), i, x) for i, x in enumerate(arr)]
        result = _quick_sort_internal(decorated, reverse)
        return [x for _, _, x in result]
    
    result = _quick_sort_internal(arr[:], reverse)
    return result


def _quick_sort_internal(arr: List, reverse: bool) -> List:
    """内部排序实现"""
    if len(arr) <= 1:
        return arr
    
    # 随机选择pivot以避免最坏情况
    pivot_idx = random.randint(0, len(arr) - 1)
    pivot = arr[pivot_idx]
    
    left = []
    middle = []
    right = []
    
    for x in arr:
        if x < pivot:
            left.append(x)
        elif x == pivot:
            middle.append(x)
        else:
            right.append(x)
    
    if reverse:
        return _quick_sort_internal(right, reverse) + middle + _quick_sort_internal(left, reverse)
    else:
        return _quick_sort_internal(left, reverse) + middle + _quick_sort_internal(right, reverse)


# ==================== 测试代码 ====================

def test_quick_sort():
    """测试快速排序算法"""
    test_cases = [
        ([], "空数组"),
        ([1], "单元素数组"),
        ([3, 1, 2], "小数组"),
        ([5, 4, 3, 2, 1], "逆序数组"),
        ([1, 2, 3, 4, 5], "已排序数组"),
        ([3, 3, 3, 3], "相同元素数组"),
        ([5, 2, 8, 1, 9, 3, 7, 4, 6], "随机数组"),
        ([-3, -1, -5, 2, 0, 4], "含负数数组"),
        ([1, 3, 2, 2, 2, 2, 2, 1, 3], "大量重复元素"),
    ]
    
    print("=" * 50)
    print("快速排序算法测试")
    print("=" * 50)
    
    for arr, description in test_cases:
        # 测试基础版本
        result_basic = quick_sort_basic(arr.copy())
        
        # 测试原地排序版本
        arr_inplace = arr.copy()
        quick_sort_inplace(arr_inplace)
        
        # 测试优化版本
        arr_optimized = arr.copy()
        quick_sort_optimized(arr_optimized)
        
        # 测试三路分区版本
        arr_three_way = arr.copy()
        quick_sort_three_way(arr_three_way)
        
        # 测试统一接口
        result_unified = quick_sort(arr)
        
        expected = sorted(arr)
        
        # 验证结果
        assert result_basic == expected, f"基础版本失败: {description}"
        assert arr_inplace == expected, f"原地版本失败: {description}"
        assert arr_optimized == expected, f"优化版本失败: {description}"
        assert arr_three_way == expected, f"三路分区版本失败: {description}"
        assert result_unified == expected, f"统一接口失败: {description}"
        
        print(f"✓ {description}: {arr} -> {expected}")
    
    # 测试降序排序
    print("\n降序排序测试:")
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quick_sort(arr, reverse=True)
    expected = sorted(arr, reverse=True)
    assert result == expected, f"降序排序失败"
    print(f"✓ 降序: {arr} -> {result}")
    
    # 测试key函数
    print("\nKey函数测试:")
    arr = ["banana", "Apple", "cherry", "date"]
    result = quick_sort(arr, key=str.lower)
    expected = sorted(arr, key=str.lower)
    assert result == expected, f"Key函数排序失败"
    print(f"✓ 按字母排序（忽略大小写）: {arr} -> {result}")
    
    print("\n所有测试通过！")


def benchmark_quick_sort():
    """性能对比测试"""
    import time
    
    print("\n" + "=" * 50)
    print("性能对比测试")
    print("=" * 50)
    
    sizes = [1000, 10000, 50000]
    
    for size in sizes:
        arr = [random.randint(1, 10000) for _ in range(size)]
        
        # 测试基础版本
        start = time.time()
        quick_sort_basic(arr.copy())
        basic_time = time.time() - start
        
        # 测试原地版本
        start = time.time()
        quick_sort_inplace(arr.copy())
        inplace_time = time.time() - start
        
        # 测试优化版本
        start = time.time()
        quick_sort_optimized(arr.copy())
        optimized_time = time.time() - start
        
        # 测试三路分区版本
        start = time.time()
        quick_sort_three_way(arr.copy())
        three_way_time = time.time() - start
        
        print(f"\n数组大小: {size}")
        print(f"  基础版本: {basic_time:.4f}s")
        print(f"  原地版本: {inplace_time:.4f}s")
        print(f"  优化版本: {optimized_time:.4f}s")
        print(f"  三路分区: {three_way_time:.4f}s")


if __name__ == "__main__":
    test_quick_sort()
    benchmark_quick_sort()
