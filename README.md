 Sistema de Navegación A*
Prototipo interactivo de búsqueda de rutas óptimas desarrollado como ejercicio para el departamento de IA Automovilística. Permite simular la navegación de un vehículo sobre un mapa en cuadrícula usando el algoritmo A*.

¿Qué hace la aplicación?
El usuario configura un mapa urbano pintando obstáculos, zonas lentas y autopistas, define un punto de origen y uno de destino, y la aplicación calcula y anima la ruta óptima en tiempo real.

Movimiento en 8 direcciones (incluye diagonales y zig-zag, no solo Manhattan)
Costes de terreno variables: autopistas (×0.5), tráfico lento (×2.5), edificios bloqueados
Visualización animada de la ruta y las celdas exploradas
Configuración completamente interactiva, sin instalar nada.

Cómo ejecutarlo
Descargar astar_navigation.html y abrirlo con doble clic en cualquier navegador. No requiere instalación ni servidor.

Referencias
Durante el desarrollo me apoyé en los siguientes recursos:

- Red Blob Games — Introduction to A* · redblobgames.com/pathfinding/a-star/introduction.html
La referencia más completa y visual para entender A*, Dijkstra y las distintas heurísticas. Muy útil para comprender la distancia Octile y el manejo de costes de terreno.
- Wikipedia — A* search algorithm · en.wikipedia.org/wiki/A*_search_algorithm
Explicación formal del algoritmo, pseudocódigo y propiedades de admisibilidad y consistencia.
- Amit's Thoughts on Pathfinding · theory.stanford.edu/~amitp/GameProgramming
Artículos de Amit Patel (Stanford) sobre distintas variantes de pathfinding y optimizaciones para mapas en cuadrícula.

Conclusiones
El ejercicio demuestra que A* es una solución sólida para sistemas de navegación: encuentra rutas óptimas de forma eficiente incluso con obstáculos complejos y costes variables.
La incorporación de movimiento diagonal y diferentes tipos de terreno acerca el prototipo a un escenario urbano real, cumpliendo todos los requisitos del enunciado.
