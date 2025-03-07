"""Test the core table functionality.
"""


from nose.tools import assert_raises, assert_equal
from django.http import Http404
from django.core.paginator import Paginator
import django_tables as tables
from django_tables.base import BaseTable


class TestTable(BaseTable):
    pass


def test_declaration():
    """
    Test defining tables by declaration.
    """

    class GeoAreaTable(TestTable):
        name = tables.Column()
        population = tables.Column()

    assert len(GeoAreaTable.base_columns) == 2
    assert 'name' in GeoAreaTable.base_columns
    assert not hasattr(GeoAreaTable, 'name')

    class CountryTable(GeoAreaTable):
        capital = tables.Column()

    assert len(CountryTable.base_columns) == 3
    assert 'capital' in CountryTable.base_columns

    # multiple inheritance
    class AddedMixin(TestTable):
        added = tables.Column()

    class CityTable(GeoAreaTable, AddedMixin):
        mayer = tables.Column()

    assert len(CityTable.base_columns) == 4
    assert 'added' in CityTable.base_columns

    # modelforms: support switching from a non-model table hierarchy to a
    # modeltable hierarchy (both base class orders)
    class StateTable1(tables.ModelTable, GeoAreaTable):
        motto = tables.Column()

    class StateTable2(GeoAreaTable, tables.ModelTable):
        motto = tables.Column()

    assert len(StateTable1.base_columns) == len(StateTable2.base_columns) == 3
    assert 'motto' in StateTable1.base_columns
    assert 'motto' in StateTable2.base_columns


def test_sort():
    class MyUnsortedTable(TestTable):
        alpha  = tables.Column()  # noqa
        beta   = tables.Column()  # noqa
        n      = tables.Column()  # noqa

    test_data = [
        {'alpha': "mmm", 'beta': "mmm", 'n': 1},
        {'alpha': "aaa", 'beta': "zzz", 'n': 2},
        {'alpha': "zzz", 'beta': "aaa", 'n': 3},
    ]

    # various different ways to say the same thing: don't sort
    assert_equal(MyUnsortedTable(test_data).order_by, ())
    assert_equal(MyUnsortedTable(test_data, order_by=None).order_by, ())
    assert_equal(MyUnsortedTable(test_data, order_by=[]).order_by, ())
    assert_equal(MyUnsortedTable(test_data, order_by=()).order_by, ())

    # values of order_by are wrapped in tuples before being returned
    assert_equal(('alpha',), MyUnsortedTable([], order_by='alpha').order_by)
    assert_equal(('beta',),  MyUnsortedTable([], order_by=('beta',)).order_by)
    assert_equal((),         MyUnsortedTable([]).order_by)

    # a rewritten order_by is also wrapped
    table = MyUnsortedTable([])
    table.order_by = 'alpha'
    assert_equal(('alpha',), table.order_by)

    # default sort order can be specified in table options
    class MySortedTable(MyUnsortedTable):
        class Meta:
            order_by = 'alpha'

    # order_by is inherited from the options if not explitly set
    table = MySortedTable(test_data)
    assert_equal(('alpha',), table.order_by)

    # ...but can be overloaded at __init___
    table = MySortedTable(test_data, order_by='beta')
    assert_equal(('beta',), table.order_by)

    # ...or rewritten later
    table = MySortedTable(test_data)
    table.order_by = 'beta'
    assert_equal(('beta',), table.order_by)

    # ...or reset to None (unsorted), ignoring the table default
    table = MySortedTable(test_data, order_by=None)
    assert_equal((), table.order_by)
    assert_equal(1, table.rows[0]['n'])


def test_column_count():
    class MyTable(TestTable):
        visbible = tables.Column(visible=True)
        hidden = tables.Column(visible=False)

    # The columns container supports the len() builtin
    assert len(MyTable([]).columns) == 1


def test_pagination():
    class BookTable(TestTable):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(1, 101):
        data.append({'name': 'Book Nr. %d' % i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert len(page.object_list) == 10
    assert page.has_previous() is False
    assert page.has_next() is True

    # integrated paginator
    books.paginate(Paginator, 10, page=1)
    # rows is now paginated
    assert len(list(books.rows.page())) == 10
    assert len(list(books.rows.all())) == 100
    # new attributes
    assert books.paginator.num_pages == 10
    assert books.page.has_previous() is False
    assert books.page.has_next() is True
    # exceptions are converted into 404s
    assert_raises(Http404, books.paginate, Paginator, 10, page=9999)
    assert_raises(Http404, books.paginate, Paginator, 10, page="abc")
