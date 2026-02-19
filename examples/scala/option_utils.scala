object OptionUtils {
  def parseInt(s: String): Option[Int] = {
    try {
      Some(s.trim.toInt)
    } catch {
      case _: NumberFormatException => None
    }
  }

  def divide(a: Double, b: Double): Option[Double] = {
    if (b == 0) None else Some(a / b)
  }

  def lookup[K, V](map: Map[K, V], key: K): Option[V] = {
    map.get(key)
  }

  def firstPositive(numbers: List[Int]): Option[Int] = {
    numbers.find(_ > 0)
  }
}

object Main extends App {
  val inputs = List("42", "hello", "17", "", "99")

  val parsed = inputs.flatMap(OptionUtils.parseInt)
  println(s"Parsed numbers: $parsed")

  val result = for {
    a <- OptionUtils.parseInt("100")
    b <- OptionUtils.parseInt("3")
    quotient <- OptionUtils.divide(a.toDouble, b.toDouble)
  } yield quotient

  println(s"Division result: $result")

  val config = Map("host" -> "localhost", "port" -> "8080")
  val host = OptionUtils.lookup(config, "host").getOrElse("unknown")
  val timeout = OptionUtils.lookup(config, "timeout").getOrElse("30")
  println(s"Host: $host, Timeout: $timeout")
}
