import kotlin.math.PI
import kotlin.math.sqrt

sealed class Shape {
    abstract fun area(): Double
    abstract fun perimeter(): Double
}

data class Circle(val radius: Double) : Shape() {
    override fun area(): Double = PI * radius * radius
    override fun perimeter(): Double = 2 * PI * radius
}

data class Rectangle(val width: Double, val height: Double) : Shape() {
    override fun area(): Double = width * height
    override fun perimeter(): Double = 2 * (width + height)
}

data class Triangle(val a: Double, val b: Double, val c: Double) : Shape() {
    override fun area(): Double {
        val s = perimeter() / 2
        return sqrt(s * (s - a) * (s - b) * (s - c))
    }

    override fun perimeter(): Double = a + b + c
}

fun describeShape(shape: Shape): String {
    return when (shape) {
        is Circle -> "Circle with radius ${shape.radius}"
        is Rectangle -> "Rectangle ${shape.width}x${shape.height}"
        is Triangle -> "Triangle with sides ${shape.a}, ${shape.b}, ${shape.c}"
    }
}

fun main() {
    val shapes = listOf(
        Circle(5.0),
        Rectangle(3.0, 4.0),
        Triangle(3.0, 4.0, 5.0)
    )

    for (shape in shapes) {
        println("${describeShape(shape)}: area=${shape.area()}, perimeter=${shape.perimeter()}")
    }
}
