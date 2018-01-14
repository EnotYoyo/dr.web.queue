CREATE TABLE IF NOT EXISTS tasks
(
  id          SERIAL NOT NULL PRIMARY KEY,
  create_time TIMESTAMP        DEFAULT now(),
  start_time  TIMESTAMP,
  exec_time   DOUBLE PRECISION DEFAULT 0.0
);

CREATE UNIQUE INDEX IF NOT EXISTS tasks_id_idx
  ON tasks (id);
