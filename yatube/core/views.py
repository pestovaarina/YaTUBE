from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    '''Ошибка 404: страница не найдена.'''
    return render(request, 'core/404.html',
                  {'path': request.path},
                  status=HTTPStatus.NOT_FOUND)


def server_error(request):
    '''Ошибка 500: внутренняя ошибка сервера.'''
    return render(request, 'core/500.html',
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)


def permission_denied(request, exception):
    '''Ошибка 403: запрос отклонён.'''
    return render(request, 'core/403.html',
                  status=HTTPStatus.FORBIDDEN)


def csrf_failure(request, reason=''):
    '''Ошибка 403: ошибка проверки CSRF.'''
    return render(request, 'core/403csrf.html')
