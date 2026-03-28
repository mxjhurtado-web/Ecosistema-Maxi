# Maxi-Designer

Herramienta de escritorio para visualizar, editar y simular flujos de chat de Maxi IA.

## Requisitos

- Python 3.10+
- PyQt6

Instalar dependencias:
```bash
pip install PyQt6
```

## Características

- **Visualización Estética**: Nodos con bordes redondeados y colores dinámicos según el tipo.
- **Canvas Infinito**: Soporte para Zoom (Rueda del ratón) y Pan (Click derecho / Arrastrar).
- **Editor de Nodos**: Doble clic en cualquier nodo para editar sus propiedades JSON.
- **Simulador Integrado**: Botón "Play" para probar la lógica del flujo paso a paso.
- **Control de Versiones**: Cada vez que exportas, se guarda un historial en la carpeta `.history`.
- **Biblioteca de Componentes**: Guarda ramas completas como archivos JSON reutilizables.
- **Exportación PDF**: Genera una captura de todo el flujo en formato profesional.

## Ejecución

```bash
python main.py
```
