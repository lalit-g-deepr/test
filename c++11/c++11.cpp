// c++11.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "pch.h"
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <regex>
#include <iostream>
#include <chrono>
#include <ctime>
#include <thread>
#include <mutex>
#include <queue>
#include <fstream>
#include <future>
#include <chrono>
#include <tuple>

using namespace std;

class LogFile
{
	std::mutex _mu;
	std::mutex _mu2;
	ofstream _f;
	std::once_flag _flag;
public:
	LogFile()
	{
		
	}

	void shared_print(string id, int value)
	{
		{
			std::call_once(_flag, [&]() {_f.open("log.txt"); });
			std::unique_lock<mutex> _Lock_nonmember1(_mu2);
				_f.open("log.txt");
		}
		std::unique_lock<mutex> locker(_mu, std::defer_lock);

		locker.lock();
		std::cout << "From " << id << ": " << value << endl;
		locker.unlock();
	}
};

//void function_1(LogFile& log)
//{
//	for (int i = 0; i > -200; i--)
//		log.shared_print("t1", i);
//}

int sum(int a, int b)
{
	return (a + b);
}

struct bankAccount
{
	int balance = 0;
public:
	bankAccount()
	{}

	bankAccount(const int _balance) :balance(_balance)
	{}

};

//TEST(Accounttest, BankAccountStartsEmpty)
//{
//	bankAccount account;
//	EXPECT_EQ(0, account.balance);
//}
//
//TEST(Accounttest2, BankAccountStartsEmpty)
//{
//	bankAccount account;
//	EXPECT_EQ(1, account.balance);
//}
//
//TEST(Accounttest3, BankAccountStartsEmpty)
//{
//	bankAccount account;
//	EXPECT_EQ(1, account.balance);
//}

//TEST(Testname, subtest_1)
//{
//	EXPECT_EQ(1, 1);
//	EXPECT_EQ(2, 2);
//}
//
//TEST(Testname, subtest_2)
//{
//	EXPECT_EQ(1, 1);
//	EXPECT_EQ(2, 2);
//}
//
//class myClass
//{
//	string id;
//public:
//	myClass(string _id) :id(_id)
//	{}
//
//	string getId() { return id; }
//};

class myClass
{
	int baseValue;
public:
	myClass(int _bv) :baseValue(_bv)
	{}
	void incrementBy(int increment)
	{
		baseValue = baseValue + increment;
	}

	int getValue() { return baseValue; }
};

//struct myClassTest : public ::testing::Test
//{
//
//
//	myClass *mt ;
//	void SetUp() { 
//		cout << "alive" << endl;
//		mt = new myClass(100); 
//	}
//	void tearDown() { 
//		cout << "dead" << endl;
//		delete mt;	}
//};
//
//TEST_F( myClassTest, incrementby5)
//{
//	mt->incrementBy(5);
//	ASSERT_EQ(mt->getValue(), 105);
//}

//test is->  1. arrange 2. act and 3. assert
//unit test self content intity


class stack {
	vector<int> vstack = {};
public:
	void push(int value)
	{
		vstack.push_back(value);
	}

	int pop()
	{
		if (!vstack.empty())
		{
			int value = vstack.back();
			vstack.pop_back();
			return value;
		}
		else
			return -1;
	}

	int size()
	{
		return vstack.size();
	}
};


//struct stackTest : public testing::Test
//{
//	stack s1;
//	void SetUp()
//	{
//		int value[] = { 1,2,3,4,5,6,7,8,9 };
//		for (auto &val : value)
//		{
//			s1.push(val);
//		}
//	}
//
//	void TearDown()
//	{}
//};
//
//
//TEST_F(stackTest, popTest)
//{
//	int lastpopperValue = 9;
//	while (lastpopperValue != 1)
//	{
//		ASSERT_EQ(s1.pop(), lastpopperValue--);
//	}
//}


deque<int> q;
mutex _mu;
condition_variable cond;

void function_1()
{
	int count = 10;
	while (count > 0)
	{
		std::unique_lock<mutex> locker(_mu);
		q.push_front(count);
		locker.unlock();
		cond.notify_all();
		count--;
	}
}

void function_2()
{
	int data = 0;
	while (data != 1)
	{
		std::unique_lock<mutex> locker(_mu);
		cond.wait(locker, []() {return !q.empty(); });
		data = q.back();
		q.pop_back();
		locker.unlock();
		cout << "t2 got value from t1: " << data << endl;
	}
}

class Dog {

	
public:
	Dog(string dogname)
	{
		m_name = dogname;
		cout << " Dog is created of name: " << m_name << endl;
	}
	
	void makeFriend(shared_ptr<Dog> dPtr)
	{
		m_pfriend = dPtr;
		if (!m_pfriend.expired())
		{
			cout << "Bus nam hi kafi hai " << m_pfriend.lock()->m_name << endl;
			cout << "use count is " << m_pfriend.use_count() << endl;
		}
	}
	void bark()
	{
		cout << "Dog " << m_name << " rules!" << endl;
	}
	~Dog()
	{
		cout << "dog named "<<m_name<<" destructor called" << endl;
	}

private:
	string m_name;
	weak_ptr<Dog> m_pfriend;
	
};

void test()
{
	unique_ptr<Dog> pDog(new Dog("Smokey"));

	pDog->bark();


}

class Cat
{
	Cat(const Cat&) {}
	//functions generated 
	// default no, default assinment yes, move const no, move assign no 
};

int factorial(std::shared_future<int> f)
{
	int res = 1;
	int n = f.get();
	for (int i = n; i > 0; i--)
		res *= i;

	cout << "result is " << res << endl;
	return res;
}

int factorial_(int N)
{
	int res = 1;
	for (size_t i = N; i > 0; i--)
	{
		res *= i;
	}
	return res;
}

std::deque<std::packaged_task<int()> > task_q;
std::mutex mu_task;
//std::condition_variable cond;

void thread_1()
{
	std::packaged_task<int()> t;
	{
		std::unique_lock<std::mutex> locker(mu_task);
		cond.wait(locker, [=]() {return !task_q.empty(); });
		t = std::move(task_q.front());
	}
	t();
}
int main(int argc, char* argv[])
{
	//std::thread t1(function_1);
	//std::thread t2(function_2);

	//t1.join();
	//t2.join();

	//testing::InitGoogleTest(&argc, argv);
	//return RUN_ALL_TESTS();
	//int i = 10;
	//auto sayHello = [&](int a, int b)->int { return a + b + i ; };

	//vector<int> arr = { 1,5,3,7,8 };
	//int total = 0;
	//for_each(arr.begin(), arr.end(), [&](int x) {total += x; });
	//cout << total << endl;
	//int x;
	//
	////std::thread t1(factorial, 4);
	////t1.join();

	//
	//std::promise<int> p;
	//std::shared_future<int> f = p.get_future();
	//std::future<int> fu = std::async(factorial, (f));
	//std::future<int> fu2 = std::async(factorial, (f));
	//std::future<int> fu3 = std::async(factorial, (f));
	//
	//p.set_value(4);
	//x = fu.get();
	
	//shared_ptr<Dog> p(new Dog("Smokey"));
	//shared_ptr<Dog> p2(new Dog("Gunner"));

	//p->makeFriend(p2);
	//p2->makeFriend(p);
	//cyclic reference, no destructor is called

	//test();
	std::ratio<1, 10> r;
	cout << std::chrono::system_clock::period::num << "/" << std::chrono::system_clock::period::den << endl;

	chrono::microseconds mi(2300);
	chrono::nanoseconds na(mi);
	chrono::milliseconds mill = chrono::duration_cast<chrono::milliseconds> (mi);

	chrono::system_clock::time_point tp = chrono::system_clock::now();
	cout << tp.time_since_epoch().count() << endl;

	tp = tp + chrono::seconds(2);
	cout << tp.time_since_epoch().count() << endl;


	chrono::steady_clock::time_point start = chrono::steady_clock::now();
	cout << "yupp!!!!" << endl;

	chrono::steady_clock::time_point end = chrono::steady_clock::now();

	chrono::steady_clock::duration d = end - start;

	if (d == chrono::steady_clock::duration::zero())
		cout << "no time elapased" << endl;

	cout << chrono::duration_cast<chrono::microseconds>(d).count() << endl;

	tuple<int, string, char> t(32, "Penny", 'a');
	cout << get<0>(t) << endl;
	cout << get<1>(t) << endl;
	cout << get<2>(t) << endl;

	get<1>(t) = "pound";
	cout << get<0>(t) << endl;
	cout << get<1>(t) << endl;
	cout << get<2>(t) << endl;

	std::thread t1(thread_1);
	//pacakged task

	std::packaged_task<int()> task(std::bind(factorial_, 6));
	std::future<int> fu = task.get_future();

	{
		std::unique_lock<std::mutex> locker(mu_task);
		task_q.push_back(std::move(task));
	}
	cond.notify_one();
	cout << "abhi abhi value "<<fu.get() << endl;
	
	t1.join();
	return 0;
}
