- Make several configs as `configs = dict[str, Config]`
- once call `configure(configs)`
- to get connection call `get_connection(name: str)` it will returns `SqlIO` object
- use methods from this class

or

- cast to `PSQL` and use specific methods of `PSQL` class
- cast to `MySQL` and use specific methods of `MySQL` class

For every connection `Config` creates only **one** connection. In case connection drops it will be recreates if possible
