import tcp from 'k6/x/tcp';
import { sleep, check } from 'k6';

const PORT = __ENV.PORT || 8356;

function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);

  return Math.floor(Math.random() * (max - min + 1)) + min;
}

const generateRandomString = (length) => {
  let result = '';
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const charactersLength = characters.length;
  
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

export const options = {
  stages: [
    { duration: '10s', target: 50 },
    { duration: '20s', target: 50 },
  ],

  thresholds: {
    checks: ['rate > 0.95'],
  },
};

export default () => {
  const createRandomString = () => {
    const randomInt = getRandomInt(1, 99)
      
    let length;
    if (randomInt <= 60){
      length = getRandomInt(1, 10)
    }else if (randomInt <= 80){
      length = getRandomInt(11, 25)
    }else if (randomInt <= 90){
      length = getRandomInt(26, 50)
    }else if (randomInt <=97){
      length = getRandomInt(51, 100)
    }else {
      length = getRandomInt(101, 200)
    }    

    const randomString = generateRandomString(length);
    
    if (randomString.length >= 2) {
      return randomString.slice(0, randomString.length - 2); 
    }
    return randomString;
  }

  const address = `exo-server:${PORT}`;
  const randomString = createRandomString()
  const message = `${randomString}\r\n`

  let conn;
  
  try {
    conn = tcp.connect(address);
  } catch (e) {
    check(null, { 'TCP connection successful': (c) => c !== null });
    return;
  }

  tcp.writeLn(conn, message)

  let res = String.fromCharCode(...tcp.read(conn, 1024))
  check(res, {
    'Received response': (r) => r && r.length > 0,
    'Echo check (Sent message)': (r) => r.includes(randomString)
  });

  tcp.close(conn);
  
  sleep(0.5); 
}