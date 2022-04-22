from functools import wraps


class Top:
    def __init__(self, get_response):
        print('Top init')
        self.get_response = get_response
        
    def __call__(self, request):
        print('Top call')
        request.set_name('Top')
        response = self.get_response(request)
        raise Exception('Top exception')
        return response

    def process_view(request, view_func, *args, **kwargs):
        print(f'Top process view: {view_func}, {args=}, {kwargs=}')


class Middle:
    def __init__(self, get_response):
        print('Middle init')
        self.get_response = get_response
        
    def __call__(self, request):
        print('Middle call')
        request.set_name('Middle')
        response = self.get_response(request)
        raise Exception('Middle exception')
        return response

    def process_view(request, view_func, *args, **kwargs):
        print(f'Middle process view: {view_func}, {args=}, {kwargs=}')


class Bottom:
    def __init__(self, get_response):
        print('Bottom init')
        self.get_response = get_response
        
    def __call__(self, request):
        print('Bottom call')
        request.set_name('Bottom')
        response = self.get_response(request)
        raise Exception('Bottom exception')
        return response

    def process_view(request, view_func, *args, **kwargs):
        print(f'Bottom process view: {view_func}, {args=}, {kwargs=}')


def exception_catcher(get_response):
    @wraps(get_response)
    def inner(request):
        print(f'I am exception catcher with {request=}')
        try:
            response = get_response(request)
            return response
        except Exception as e:
            print(f'exception: {e}')
            return None
    return inner


class BaseHandler:
    middleware_classes = [Top, Middle, Bottom]
    _view_middleware = None
    _middleware_chain = None

    def load_middleware(self):
        """
        对每一层中间件，其实例会接受request参数，执行__call__方法，在__call__中调用了传入的get_response可调用对象
        因为get_response和中间件实例都接受request参数，因此get_response和中间件本质上没有区别
        所以任何一个接受request参数的类或者函数都可以作为另外一个中间件实例初始化的参数
        """
        self._view_middleware = []
        # 初始的handler为_get_response方法
        handler = self._get_response
        for middleware in reversed(self.middleware_classes):
            print('initial middleware')
            # 初始化实例，此时
            mw_instance = middleware(handler)

            if hasattr(mw_instance, 'process_view'):
                self._view_middleware.insert(0, mw_instance.process_view)

            print('wraps mw_instance start')
            # 将mw_instance实例放置在装饰器内
            handler = exception_catcher(mw_instance)
            print('wraps mw_instance end')

        # 此时的中间件链为 wrapper@top[wrapper@middle[wrapper@bottom[_get_response(request)]]]
        # wrapper表示exception_catcher装饰器，小写的top, middle, bottom为实例
        # 执行的时候从外而内，执行实例的__call__方法
        # 展开形式如下
        """
        try:
            # 第一层Top
            print('Top call')
            request.set_name('Top')
            # response = self.get_response(request)

                # 第二层Middle
                try:
                    print('Middle call')
                    request.set_name('Middle')
                    # response = self.get_response(request)

                        # 第三层 Bottom
                        try:
                            print('Bottom call')
                            request.set_name('Bottom')
                            # response = self.get_response(request)

                                # 最内层 执行的是_get_response

                            raise Exception('Bottom exception')
                            return response
                        except Exception as e:
                            print(f'exception: {e}')
                            return None

                    raise Exception('Middle exception')
                    return response
                except Exception as e:
                    print(f'exception: {e}')
                    return None

            raise Exception('Top exception')
            return response
        except Exception as e:
            print(f'exception: {e}')
            return None
        """
        self._middleware_chain = handler

    def get_response(self, request):
        print('execute _middleware_chain start')
        response = self._middleware_chain(request)
        print('execute _middleware_chain end')
        return response

    def _get_response(self, request):
        def view_func():
            print('I am view func')

        print('I am the most inner get response method')
        response = None

        # 从顶至下执行各中间件的process_view，如果没有提前返回，最后执行view_func
        for process_view in self._view_middleware:
            response = process_view(request, view_func, ['a', 'b'], test='123')
            if response:
                break

        if response is None:
            response = view_func()

        return response


class Request:
    def __init__(self):
        self.name = 'default'

    def set_name(self, name):
        print(f'previous name: {self.name}, new name: {name}')
        self.name = name

    def __str__(self):
        return f'I am a request with name: {self.name}'


class WSGIHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_middleware()

    def __call__(self):
        request = Request()
        response = self.get_response(request)
        return response


if __name__ == '__main__':
    wsgi = WSGIHandler()
    wsgi()
