A `File` object is rarely used directly by end users, but it is a common base class for `Input` and `Data` structures that may contain files. The `File` object enables transparent serialization of binary file data for serialization to `.json`, `.yaml`, or `.toml` which makes saving data structures to disk in a human-readable format or sending them over HTTP seamless even when they contain binary data.

::: qcdata.Files
