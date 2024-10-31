from loader import dp
from .is_admin import IsAdminFilter
from .is_manager import IsManagerFilter

if __name__ == "filters":
    dp.filters_factory.bind(IsAdminFilter)
    dp.filters_factory.bind(IsManagerFilter)
