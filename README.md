reader queue

reader.request => outstanding, async, event message
reader.response => has waiting, be protected by reader and writer mutex

mutex is for reader.response and writer

