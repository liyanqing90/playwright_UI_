import time
import pytest
from playwright.sync_api import sync_playwright
from page_objects.base_page import BasePage
from utils.performance_manager import performance_manager
from utils.logger import logger


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_performance_test(self):
        """设置性能测试"""
        # 重置性能统计
        performance_manager.reset_stats()
        # 优化为测试环境
        performance_manager.optimize_for_environment("test")
        yield
        # 输出性能统计
        stats = performance_manager.get_performance_stats()
        logger.info(f"测试完成，性能统计: {stats}")
    
    def test_element_locator_performance(self, page):
        """测试元素定位性能"""
        base_page = BasePage(page)
        
        # 导航到测试页面
        page.goto("https://www.baidu.com")
        
        # 测试多次定位同一元素（应该命中缓存）
        selector = "input[name='wd']"
        
        start_time = time.time()
        
        # 第一次定位（缓存未命中）
        locator1 = base_page._locator(selector)
        first_locate_time = time.time() - start_time
        
        # 第二次定位（应该命中缓存）
        cache_start = time.time()
        locator2 = base_page._locator(selector)
        cache_locate_time = time.time() - cache_start
        
        # 验证缓存效果
        assert cache_locate_time < first_locate_time, "缓存应该提高定位速度"
        
        # 获取性能统计
        stats = performance_manager.get_performance_stats()
        assert stats['cache_hits'] > 0, "应该有缓存命中"
        assert stats['cache_hit_rate'] > 0, "缓存命中率应该大于0"
        
        logger.info(f"首次定位耗时: {first_locate_time:.3f}s")
        logger.info(f"缓存定位耗时: {cache_locate_time:.3f}s")
        logger.info(f"性能提升: {((first_locate_time - cache_locate_time) / first_locate_time * 100):.1f}%")
    
    def test_batch_element_operations(self, page):
        """测试批量元素操作性能"""
        base_page = BasePage(page)
        
        # 导航到测试页面
        page.goto("https://www.baidu.com")
        
        # 定义多个选择器
        selectors = [
            "input[name='wd']",
            "input[type='submit']",
            "#kw",
            "#su",
            ".s_ipt"
        ]
        
        start_time = time.time()
        
        # 批量定位元素
        locators = []
        for selector in selectors:
            try:
                locator = base_page._locator(selector)
                locators.append(locator)
            except Exception as e:
                logger.warning(f"定位元素失败: {selector}, 错误: {e}")
        
        total_time = time.time() - start_time
        
        # 验证性能
        assert total_time < 10.0, "批量操作应该在10秒内完成"
        assert len(locators) > 0, "应该成功定位到至少一个元素"
        
        # 获取性能统计
        stats = performance_manager.get_performance_stats()
        logger.info(f"批量操作耗时: {total_time:.3f}s")
        logger.info(f"平均每个元素耗时: {(total_time / len(selectors)):.3f}s")
        logger.info(f"操作统计: {stats}")
    
    def test_cache_effectiveness(self, page):
        """测试缓存有效性"""
        base_page = BasePage(page)
        
        # 导航到测试页面
        page.goto("https://www.baidu.com")
        
        selector = "input[name='wd']"
        
        # 多次定位同一元素
        for i in range(5):
            base_page._locator(selector)
        
        # 检查缓存统计
        stats = performance_manager.get_performance_stats()
        
        # 应该有4次缓存命中（第一次是缓存未命中）
        assert stats['cache_hits'] >= 4, f"期望至少4次缓存命中，实际: {stats['cache_hits']}"
        assert stats['cache_hit_rate'] >= 80, f"缓存命中率应该至少80%，实际: {stats['cache_hit_rate']:.1f}%"
        
        logger.info(f"缓存测试完成: {stats}")
    
    def test_performance_monitoring(self, page):
        """测试性能监控功能"""
        base_page = BasePage(page)
        
        # 导航到测试页面
        page.goto("https://www.baidu.com")
        
        # 执行一些操作
        selector = "input[name='wd']"
        
        # 模拟慢操作（通过增加超时时间）
        try:
            base_page._locator("non-existent-element", timeout=1000)
        except Exception:
            pass  # 预期会失败
        
        # 正常操作
        base_page._locator(selector)
        
        # 检查监控统计
        stats = performance_manager.get_performance_stats()
        
        assert stats['total_operations'] >= 2, "应该记录至少2次操作"
        
        logger.info(f"性能监控测试完成: {stats}")
    
    def test_configuration_loading(self):
        """测试配置加载"""
        # 测试配置获取
        cache_timeout = performance_manager.get_cache_timeout()
        assert isinstance(cache_timeout, int), "缓存超时应该是整数"
        assert cache_timeout > 0, "缓存超时应该大于0"
        
        max_screenshots = performance_manager.get_max_screenshots()
        assert isinstance(max_screenshots, int), "最大截图数应该是整数"
        assert max_screenshots > 0, "最大截图数应该大于0"
        
        is_cache_enabled = performance_manager.is_cache_enabled()
        assert isinstance(is_cache_enabled, bool), "缓存启用状态应该是布尔值"
        
        logger.info("配置加载测试通过")
    
    def test_environment_optimization(self):
        """测试环境优化"""
        # 测试CI环境优化
        performance_manager.optimize_for_environment("ci")
        max_screenshots = performance_manager.get_max_screenshots()
        assert max_screenshots <= 10, "CI环境应该限制截图数量"
        
        # 测试调试环境优化
        performance_manager.optimize_for_environment("debug")
        should_log = performance_manager.should_log_cache_hits()
        assert should_log == True, "调试环境应该启用详细日志"
        
        # 测试生产环境优化
        performance_manager.optimize_for_environment("production")
        cache_timeout = performance_manager.get_cache_timeout()
        assert cache_timeout >= 60, "生产环境应该使用更长的缓存时间"
        
        logger.info("环境优化测试通过")


if __name__ == "__main__":
    # 运行性能测试
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_instance = TestPerformance()
        test_instance.setup_performance_test()
        
        try:
            test_instance.test_configuration_loading()
            test_instance.test_environment_optimization()
            test_instance.test_element_locator_performance(page)
            test_instance.test_batch_element_operations(page)
            test_instance.test_cache_effectiveness(page)
            test_instance.test_performance_monitoring(page)
            
            print("所有性能测试通过！")
            
        except Exception as e:
            print(f"性能测试失败: {e}")
        
        finally:
            browser.close()
            # 输出最终统计
            final_stats = performance_manager.get_performance_stats()
            print(f"最终性能统计: {final_stats}")