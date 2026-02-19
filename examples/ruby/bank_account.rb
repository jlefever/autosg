class BankAccount
  attr_reader :owner, :balance

  def initialize(owner, balance = 0)
    @owner = owner
    @balance = balance
  end

  def deposit(amount)
    raise ArgumentError, "Amount must be positive" unless amount > 0

    @balance += amount
    self
  end

  def withdraw(amount)
    raise ArgumentError, "Amount must be positive" unless amount > 0
    raise "Insufficient funds" if amount > @balance

    @balance -= amount
    self
  end

  def transfer(other_account, amount)
    withdraw(amount)
    other_account.deposit(amount)
  end

  def to_s
    "#{@owner}: $#{'%.2f' % @balance}"
  end
end

alice = BankAccount.new("Alice", 1000)
bob = BankAccount.new("Bob", 500)

alice.deposit(200)
alice.transfer(bob, 150)

puts alice
puts bob
