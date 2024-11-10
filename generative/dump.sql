SQL Dump for Student Database

-- Crear tabla de alumnos
CREATE TABLE alumnos (
                         id INT PRIMARY KEY AUTO_INCREMENT,
                         nombre VARCHAR(50),
                         apellido VARCHAR(50),
                         legajo VARCHAR(5)
);

-- Crear tabla de cursadas
CREATE TABLE cursadas (
                          id INT PRIMARY KEY AUTO_INCREMENT,
                          alumno_id INT,
                          cuatrimestre INT,
                          anio INT,
                          nota INT,
                          FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
);

-- Insertar alumnos
INSERT INTO alumnos (nombre, apellido, legajo) VALUES
                                                   ('Juan', 'Pérez', '10001'),
                                                   ('María', 'González', '10002'),
                                                   ('Carlos', 'Rodríguez', '10003'),
                                                   ('Ana', 'Martínez', '10004'),
                                                   ('Luis', 'Sánchez', '10005'),
                                                   ('Laura', 'Fernández', '10006'),
                                                   ('Diego', 'López', '10007'),
                                                   ('Sofía', 'Torres', '10008'),
                                                   ('Pablo', 'Díaz', '10009'),
                                                   ('Valentina', 'Ruiz', '10010'),
                                                   ('Martín', 'García', '10011'),
                                                   ('Lucía', 'Romano', '10012'),
                                                   ('Federico', 'Álvarez', '10013'),
                                                   ('Carolina', 'Acosta', '10014'),
                                                   ('Eduardo', 'Morales', '10015'),
                                                   ('Camila', 'Flores', '10016'),
                                                   ('Gabriel', 'Benítez', '10017'),
                                                   ('Victoria', 'Castro', '10018'),
                                                   ('Andrés', 'Navarro', '10019'),
                                                   ('Julia', 'Ortiz', '10020'),
                                                   ('Miguel', 'Giménez', '10021'),
                                                   ('Florencia', 'Silva', '10022'),
                                                   ('Ricardo', 'Vargas', '10023'),
                                                   ('Paula', 'Ramos', '10024'),
                                                   ('Hernán', 'Medina', '10025'),
                                                   ('Marina', 'Cruz', '10026'),
                                                   ('Ignacio', 'Herrera', '10027'),
                                                   ('Natalia', 'Mendoza', '10028'),
                                                   ('Daniel', 'Paz', '10029'),
                                                   ('Agustina', 'Luna', '10030'),
                                                   ('Roberto', 'Ríos', '10031'),
                                                   ('Cecilia', 'Rojas', '10032'),
                                                   ('Gonzalo', 'Peralta', '10033'),
                                                   ('Mariana', 'Vega', '10034'),
                                                   ('Sebastián', 'Campos', '10035'),
                                                   ('Daniela', 'Molina', '10036'),
                                                   ('Fernando', 'Aguirre', '10037'),
                                                   ('Valeria', 'Delgado', '10038'),
                                                   ('Javier', 'Miranda', '10039'),
                                                   ('Luciana', 'Pacheco', '10040'),
                                                   ('Marcos', 'Guerrero', '10041'),
                                                   ('Antonella', 'Sosa', '10042'),
                                                   ('Lucas', 'Villalba', '10043'),
                                                   ('Belén', 'Suárez', '10044'),
                                                   ('Gustavo', 'Romero', '10045'),
                                                   ('Celeste', 'Coronel', '10046'),
                                                   ('Alejandro', 'Gómez', '10047'),
                                                   ('Julieta', 'Vera', '10048'),
                                                   ('Leonardo', 'Montenegro', '10049'),
                                                   ('Melina', 'Quiroga', '10050'),
                                                   ('Tomás', 'Escobar', '10051'),
                                                   ('Rocío', 'Cáceres', '10052'),
                                                   ('Matías', 'Arce', '10053'),
                                                   ('Candela', 'Ledesma', '10054'),
                                                   ('Franco', 'Ojeda', '10055'),
                                                   ('Aldana', 'Ibáñez', '10056'),
                                                   ('Bruno', 'Chávez', '10057'),
                                                   ('Carla', 'Duarte', '10058'),
                                                   ('Nicolás', 'Méndez', '10059'),
                                                   ('Micaela', 'Figueroa', '10060');

-- Insertar cursadas (la mayoría cursa una vez, algunos recursan)
INSERT INTO cursadas (alumno_id, cuatrimestre, anio, nota) VALUES
-- Cursadas 2020
(1, 1, 2020, 7),
(2, 1, 2020, 4),
(3, 1, 2020, 8),
(4, 2, 2020, 6),
(5, 2, 2020, 7),

-- Cursadas 2021
(6, 1, 2021, 8),
(7, 1, 2021, 9),
(8, 1, 2021, 5),
(9, 2, 2021, 7),
(10, 2, 2021, 8),
(2, 2, 2021, 7), -- Recursa

-- Cursadas 2022
(11, 1, 2022, 6),
(12, 1, 2022, 8),
(13, 1, 2022, 7),
(14, 2, 2022, 9),
(15, 2, 2022, 4),
(8, 2, 2022, 7), -- Recursa

-- Cursadas 2023
(16, 1, 2023, 8),
(17, 1, 2023, 7),
(18, 1, 2023, 6),
(19, 1, 2023, 8),
(20, 1, 2023, 9),
(21, 1, 2023, 7),
(22, 1, 2023, 8),
(23, 2, 2023, 6),
(24, 2, 2023, 7),
(25, 2, 2023, 8),
(26, 2, 2023, 9),
(27, 2, 2023, 7),
(28, 2, 2023, 6),
(29, 2, 2023, 8),
(15, 2, 2023, 7), -- Recursa

-- Cursadas 2024
(30, 1, 2024, 7),
(31, 1, 2024, 8),
(32, 1, 2024, 9),
(33, 1, 2024, 6),
(34, 1, 2024, 7),
(35, 1, 2024, 8),
(36, 1, 2024, 7),
(37, 1, 2024, 6),
(38, 1, 2024, 8),
(39, 1, 2024, 7),
(40, 1, 2024, 9);