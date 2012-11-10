drop table if exists users;
create table users (
  id integer primary key autoincrement,
  phone string not null
);
drop table if exists requests;
create table requests (
  id integer primary key autoincrement,
  uid integer not null,
  url string not null,
  foreign key (uid) references users(id)
);