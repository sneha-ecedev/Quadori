"""Shared city choices for Quadori's India-only travel searches."""

INDIAN_CITY_NAMES = (
    'Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Goa', 'Lucknow', 'Varanasi', 'Agra',
    'Surat', 'Vadodara', 'Nagpur', 'Indore', 'Bhopal', 'Patna', 'Ranchi',
    'Bhubaneswar', 'Guwahati', 'Chandigarh', 'Amritsar', 'Kochi',
    'Thiruvananthapuram', 'Coimbatore', 'Visakhapatnam', 'Vijayawada',
    'Mysuru', 'Udaipur', 'Jodhpur', 'Mangaluru', 'Madurai', 'Nashik',
    'Jammu', 'Srinagar', 'Dehradun', 'Shimla', 'Raipur', 'Thane',
)

INDIAN_CITY_CHOICES = (('', 'Select city'),) + tuple(
    (city, city) for city in INDIAN_CITY_NAMES
)
