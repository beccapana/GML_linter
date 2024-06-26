// Пример кода на GML для тестирования линтера

// Слишком длинная строка (больше 80 символов)
var tooLongLine = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam efficitur nisi at ultrices imperdiet.";

// Ошибки в отступах
if (true) {
    show_message("Hello"); // Табуляция вместо пробелов
}

// Пробелы после запятой
var array = [1,2,3,4];

// Отсутствие пробела после запятой (будет исправлено)
array = [1, 2, 3, 4];

// Отсутствие пробела перед и после скобок
var noSpaceInBrackets = [1,2,3,4];

// Пропущенные точки с запятой
var missingSemicolon = 1
show_message("Hello");

// Переменная объявлена без инициализации
var uninitializedVar;

// Ошибки в именовании переменных и функций (не camelCase)
var InvalidVariableName = 10;

// Неиспользуемая переменная
var unusedVar = 5;

// Синтаксическая ошибка в условии
if (true // забыта закрывающая скобка
{
    show_message("Syntax error");
}

// Пробелы вокруг операторов
var operation = 5+3;

// Ошибки в отступах
for (var i = 0; i < 10; i++) {
    show_message("Loop iteration: " + i);
}

// Длинный комментарий (больше 80 символов)
// Этот комментарий содержит несколько слов, которые должны быть перенесены на следующую строку, чтобы соблюсти длину строки в 80 символов.

// Пустая строка с пробелами в конце
var emptyLineWithSpaces = "Some value";  

// Правильные пробелы вокруг скобок
var spacedBrackets = [ 1, 2, 3, 4 ];

// Проверка на пропуск символа
var a=5;

// Переменная объявлена, но не используется
var unusedVariable;

// Синтаксическая ошибка в управляющем операторе
while (true) {
    show_message("While loop"); // отсутствует закрывающая скобка
}

// Это не camelCase, имя переменной не соответствует соглашению о именовании
var NonCamelCaseVariable = 10;

// Конец тест кейсов
